from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from oscar.core.loading import get_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.common.currency import (
    currency_for_country,
    is_supported_currency,
    normalize_country_code,
    normalize_currency_code,
    resolve_display_currency,
)
from apps.common.products import serialize_product_card
from apps.inventory.services import InventoryReservationError, sync_basket_line_reservation
from apps.notifications.services import queue_password_changed_email, queue_password_reset_email

from .checkout_utils import build_checkout_payload, get_checkout_session, serialize_country
from .order_serializers import OrderSummarySerializer
from .review_serializers import get_review_model, public_product_queryset, review_payload
from .wishlist_serializers import (
    get_default_wishlist,
    get_wishlist_model,
    user_wishlist_queryset,
    wishlist_detail_payload,
    wishlist_line_payload,
)


SAVED_ITEMS_SESSION_KEY = 'storefront_saved_items'
RECENTLY_VIEWED_SESSION_KEY = 'storefront_recently_viewed_product_ids'

ALLOWED_STOREFRONT_ANALYTICS_EVENTS = {
    'storefront.page_view',
    'storefront.product_view',
    'storefront.search_submitted',
    'storefront.image_search_submitted',
    'storefront.cart_item_added',
    'storefront.cart_line_updated',
    'storefront.cart_item_removed',
    'storefront.saved_for_later',
    'storefront.saved_moved_to_cart',
    'storefront.saved_item_removed',
    'storefront.voucher_applied',
    'storefront.voucher_removed',
    'storefront.order_confirmation_viewed',
}


def _money_payload(value) -> float:
    if value is None:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal('0.01')))


def _user_address_payload(address) -> dict:
    return {
        'id': address.id,
        'title': address.title or '',
        'first_name': address.first_name or '',
        'last_name': address.last_name or '',
        'line1': address.line1 or '',
        'line2': address.line2 or '',
        'line3': address.line3 or '',
        'line4': address.line4 or '',
        'state': address.state or '',
        'postcode': address.postcode or '',
        'country': serialize_country(address.country) if address.country_id else None,
        'country_code': address.country_id or '',
        'phone_number': str(address.phone_number or ''),
        'notes': address.notes or '',
        'is_default_for_shipping': address.is_default_for_shipping,
        'is_default_for_billing': address.is_default_for_billing,
    }


def _saved_items(request, display_currency: str | None = None) -> list[dict]:
    if request.user.is_authenticated:
        wishlist = get_default_wishlist(request.user, create=False)
        if not wishlist:
            return []
        payload = []
        for line in wishlist.lines.select_related('product').all():
            line_payload = wishlist_line_payload(line, display_currency=display_currency)
            payload.append(
                {
                    'id': line.id,
                    'quantity': line.quantity,
                    'date_saved': wishlist.date_created,
                    'wishlist_id': wishlist.id,
                    'wishlist_item': line_payload,
                    'product': line_payload.get('product'),
                }
            )
        return payload

    Product = apps.get_model('catalogue', 'Product')
    items = request.session.get(SAVED_ITEMS_SESSION_KEY, [])
    product_ids = [item.get('product_id') for item in items if item.get('product_id')]
    products = {
        product.id: product
        for product in Product.objects.filter(id__in=product_ids).prefetch_related('stockrecords', 'images', 'categories')
    }
    payload = []
    for item in items:
        product = products.get(item.get('product_id'))
        if not product:
            continue
        payload.append(
            {
                'id': item['id'],
                'quantity': item.get('quantity', 1),
                'date_saved': item.get('date_saved', ''),
                'product': serialize_product_card(product, display_currency=display_currency),
            }
        )
    return payload


def _save_items(request, items: list[dict]):
    request.session[SAVED_ITEMS_SESSION_KEY] = items
    request.session.modified = True


def _offer_payload(offer) -> dict:
    condition = getattr(offer, 'condition', None)
    benefit = getattr(offer, 'benefit', None)
    return {
        'id': offer.id,
        'name': offer.name,
        'slug': offer.slug,
        'description': offer.description or '',
        'offer_type': offer.offer_type,
        'status': offer.status,
        'exclusive': offer.exclusive,
        'priority': offer.priority,
        'start_datetime': offer.start_datetime.isoformat() if offer.start_datetime else None,
        'end_datetime': offer.end_datetime.isoformat() if offer.end_datetime else None,
        'redirect_url': offer.redirect_url or '',
        'condition': _offer_component_payload(condition) if condition else None,
        'benefit': _offer_component_payload(benefit) if benefit else None,
    }


def _range_payload(range_obj) -> dict:
    return {
        'id': range_obj.id,
        'name': range_obj.name,
        'slug': range_obj.slug,
        'description': range_obj.description or '',
        'is_public': range_obj.is_public,
        'includes_all_products': range_obj.includes_all_products,
        'num_products': range_obj.num_products(),
    }


def _offer_component_payload(component) -> dict:
    fallback_name = f'{component.type} offer rule'
    range_obj = getattr(component, 'range', None)
    try:
        name = component.name
    except Exception:
        name = fallback_name
    try:
        description = component.description
    except Exception:
        description = fallback_name
    return {
        'id': component.id,
        'type': component.type,
        'value': _money_payload(component.value),
        'name': name or fallback_name,
        'description': description or fallback_name,
        'range': _range_payload(range_obj) if range_obj else None,
    }


class VoucherApplyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = str(request.data.get('code', '')).strip()
        if not code:
            raise serializers.ValidationError({'code': 'Voucher code is required.'})

        Voucher = apps.get_model('voucher', 'Voucher')
        voucher = get_object_or_404(Voucher, code__iexact=code)
        if not voucher.is_active():
            raise serializers.ValidationError({'code': 'This voucher is not active.'})
        if not voucher.is_available_for_basket(request.basket):
            raise serializers.ValidationError({'code': 'This voucher cannot be applied to this basket.'})
        if request.user.is_authenticated and not voucher.is_available_to_user(request.user):
            raise serializers.ValidationError({'code': 'This voucher is not available for this account.'})

        if request.basket.pk is None:
            request.basket.save()
        request.basket.vouchers.add(voucher)
        voucher.num_basket_additions += 1
        voucher.save(update_fields=['num_basket_additions'])
        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request))


class VoucherRemoveAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, voucher_id: int):
        Voucher = apps.get_model('voucher', 'Voucher')
        voucher = get_object_or_404(Voucher, id=voucher_id)
        if request.basket.pk is None:
            return Response(build_checkout_payload(request))
        request.basket.vouchers.remove(voucher)
        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request))


class OfferCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        Offer = apps.get_model('offer', 'ConditionalOffer')
        now = timezone.now()
        offers = Offer.objects.filter(status=Offer.OPEN).filter(
            Q(start_datetime__isnull=True) | Q(start_datetime__lte=now),
            Q(end_datetime__isnull=True) | Q(end_datetime__gte=now),
        ).order_by('priority', 'name')
        return Response({'results': [_offer_payload(offer) for offer in offers]})


class OfferDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug: str):
        Offer = apps.get_model('offer', 'ConditionalOffer')
        now = timezone.now()
        offer = get_object_or_404(
            Offer.objects.filter(status=Offer.OPEN).filter(
                Q(start_datetime__isnull=True) | Q(start_datetime__lte=now),
                Q(end_datetime__isnull=True) | Q(end_datetime__gte=now),
            ),
            slug=slug,
        )
        return Response({'offer': _offer_payload(offer)})


class CatalogRangeDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug: str):
        Range = apps.get_model('offer', 'Range')
        range_obj = get_object_or_404(Range, slug=slug, is_public=True)
        products = range_obj.all_products().filter(is_public=True).exclude(structure='parent')[:60]
        display_currency = resolve_display_currency(request)
        return Response(
            {
                'range': _range_payload(range_obj),
                'results': [serialize_product_card(product, display_currency=display_currency) for product in products],
            }
        )


class SavedItemsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'results': _saved_items(request, display_currency=resolve_display_currency(request))})


class BasketLineSaveForLaterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, line_id: int):
        if request.basket.pk is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        line = get_object_or_404(request.basket.lines.select_related('product'), id=line_id)
        if request.user.is_authenticated:
            wishlist = get_default_wishlist(request.user, create=True)
            wishlist_line, created = wishlist.lines.get_or_create(
                product=line.product,
                defaults={'title': line.product.get_title(), 'quantity': line.quantity},
            )
            if not created:
                wishlist_line.quantity += line.quantity
                wishlist_line.title = line.product.get_title()
                wishlist_line.save(update_fields=['quantity', 'title'])
            line.delete()
            payload = build_checkout_payload(request)
            payload['saved'] = {'results': _saved_items(request, display_currency=resolve_display_currency(request))}
            return Response(payload)
        items = request.session.get(SAVED_ITEMS_SESSION_KEY, [])
        saved_id = max([item.get('id', 0) for item in items] or [0]) + 1
        items = [item for item in items if item.get('product_id') != line.product_id]
        items.append(
            {
                'id': saved_id,
                'product_id': line.product_id,
                'quantity': line.quantity,
                'date_saved': timezone.now().isoformat(),
            }
        )
        line.delete()
        _save_items(request, items)
        payload = build_checkout_payload(request)
        payload['saved'] = {'results': _saved_items(request, display_currency=resolve_display_currency(request))}
        return Response(payload)


class SavedItemMoveToCartAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, saved_line_id: int):
        if request.user.is_authenticated:
            wishlist = get_default_wishlist(request.user, create=False)
            if not wishlist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            saved_line = get_object_or_404(wishlist.lines.select_related('product'), id=saved_line_id)
            if not saved_line.product:
                return Response(status=status.HTTP_404_NOT_FOUND)
            try:
                line, _ = request.basket.add_product(saved_line.product, quantity=saved_line.quantity)
                sync_basket_line_reservation(line)
            except (InventoryReservationError, ValueError) as exc:
                raise serializers.ValidationError({'saved_item': str(exc)}) from exc
            saved_line.delete()
            payload = build_checkout_payload(request)
            payload['saved'] = {'results': _saved_items(request, display_currency=resolve_display_currency(request))}
            return Response(payload)
        items = request.session.get(SAVED_ITEMS_SESSION_KEY, [])
        item = next((entry for entry in items if entry.get('id') == saved_line_id), None)
        if item is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        Product = apps.get_model('catalogue', 'Product')
        product = get_object_or_404(Product, id=item['product_id'])
        try:
            line, _ = request.basket.add_product(product, quantity=item.get('quantity', 1))
            sync_basket_line_reservation(line)
        except (InventoryReservationError, ValueError) as exc:
            raise serializers.ValidationError({'saved_item': str(exc)}) from exc
        _save_items(request, [entry for entry in items if entry.get('id') != saved_line_id])
        payload = build_checkout_payload(request)
        payload['saved'] = {'results': _saved_items(request, display_currency=resolve_display_currency(request))}
        return Response(payload)


class SavedItemDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, saved_line_id: int):
        if request.user.is_authenticated:
            wishlist = get_default_wishlist(request.user, create=False)
            if wishlist:
                wishlist.lines.filter(id=saved_line_id).delete()
            return Response({'results': _saved_items(request, display_currency=resolve_display_currency(request))})
        items = request.session.get(SAVED_ITEMS_SESSION_KEY, [])
        _save_items(request, [entry for entry in items if entry.get('id') != saved_line_id])
        return Response({'results': _saved_items(request, display_currency=resolve_display_currency(request))})


class WishListItemMoveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, wishlist_id: int, product_id: int):
        target_id = request.data.get('target_wishlist_id')
        if not target_id:
            raise serializers.ValidationError({'target_wishlist_id': 'Target wishlist is required.'})
        source = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        target = get_object_or_404(user_wishlist_queryset(request.user), id=target_id)
        line = get_object_or_404(source.lines.all(), product_id=product_id)
        target.lines.get_or_create(product=line.product)
        line.delete()
        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        return Response(
            {
                'source': wishlist_detail_payload(source, default_wishlist_id=default_wishlist_id),
                'target': wishlist_detail_payload(target, default_wishlist_id=default_wishlist_id),
            }
        )


class SharedWishListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, key: str):
        WishList = get_wishlist_model()
        signer = signing.Signer(salt='storefront-wishlist-share')
        try:
            wishlist_id = signer.unsign(key)
            wishlist = get_object_or_404(WishList.objects.select_related('owner'), id=wishlist_id)
        except signing.BadSignature:
            wishlist = get_object_or_404(WishList.objects.select_related('owner'), key=key)
        if wishlist.visibility not in {wishlist.PUBLIC, wishlist.SHARED}:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({'wishlist': wishlist_detail_payload(wishlist, display_currency=resolve_display_currency(request))})


class WishListShareAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, wishlist_id: int):
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        visibility = request.data.get('visibility') or wishlist.SHARED
        if visibility not in {wishlist.SHARED, wishlist.PUBLIC}:
            raise serializers.ValidationError({'visibility': 'Use Shared or Public for share links.'})
        update_fields = ['visibility']
        if request.data.get('regenerate_key'):
            wishlist.key = wishlist.__class__.random_key()
            update_fields.append('key')
        wishlist.visibility = visibility
        wishlist.save(update_fields=update_fields)
        return Response(
            {
                'wishlist': wishlist_detail_payload(wishlist, display_currency=resolve_display_currency(request)),
                'share_key': wishlist.key,
                'share_path': f'/api/v1/wishlists/shared/{wishlist.key}/',
            }
        )


class AddressSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=64)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    line1 = serializers.CharField(max_length=255)
    line2 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    line3 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    line4 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    state = serializers.CharField(required=False, allow_blank=True, max_length=255)
    postcode = serializers.CharField(required=False, allow_blank=True, max_length=64)
    country_code = serializers.CharField(max_length=2)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=32)
    notes = serializers.CharField(required=False, allow_blank=True)
    is_default_for_shipping = serializers.BooleanField(required=False, default=False)
    is_default_for_billing = serializers.BooleanField(required=False, default=False)

    def validate_country_code(self, value):
        Country = apps.get_model('address', 'Country')
        try:
            return Country.objects.get(iso_3166_1_a2=value.upper())
        except Country.DoesNotExist as exc:
            raise serializers.ValidationError('Unknown country code.') from exc

    def save(self, *, user, instance=None):
        data = self.validated_data.copy()
        country = data.pop('country_code')
        defaults = {
            **data,
            'country': country,
            'user': user,
        }
        if instance is None:
            UserAddress = apps.get_model('address', 'UserAddress')
            instance = UserAddress(**defaults)
        else:
            for field, value in defaults.items():
                setattr(instance, field, value)
        instance.save()
        return instance


class AccountAddressCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.all().order_by('-is_default_for_shipping', '-is_default_for_billing', '-date_created')
        return Response({'results': [_user_address_payload(address) for address in addresses]})

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save(user=request.user)
        return Response({'address': _user_address_payload(address)}, status=status.HTTP_201_CREATED)


class AccountAddressDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, address_id):
        return get_object_or_404(request.user.addresses.all(), id=address_id)

    def get(self, request, address_id: int):
        return Response({'address': _user_address_payload(self.get_object(request, address_id))})

    def patch(self, request, address_id: int):
        address = self.get_object(request, address_id)
        serializer = AddressSerializer(instance=address, data={**_user_address_payload(address), **request.data}, partial=True)
        serializer.is_valid(raise_exception=True)
        address = serializer.save(user=request.user, instance=address)
        return Response({'address': _user_address_payload(address)})

    def delete(self, request, address_id: int):
        self.get_object(request, address_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountAddressDefaultShippingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, address_id: int):
        address = get_object_or_404(request.user.addresses.all(), id=address_id)
        address.is_default_for_shipping = True
        address.save()
        return Response({'address': _user_address_payload(address)})


class AccountAddressDefaultBillingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, address_id: int):
        address = get_object_or_404(request.user.addresses.all(), id=address_id)
        address.is_default_for_billing = True
        address.save()
        return Response({'address': _user_address_payload(address)})


class CheckoutAddressCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.all().order_by('-is_default_for_shipping', '-date_created')
        return Response({'results': [_user_address_payload(address) for address in addresses]})


class CheckoutUseShippingAddressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        address = get_object_or_404(request.user.addresses.all(), id=request.data.get('address_id'))
        get_checkout_session(request).ship_to_user_address(address)
        return Response(build_checkout_payload(request))


class CheckoutUseBillingAddressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        address = get_object_or_404(request.user.addresses.all(), id=request.data.get('address_id'))
        get_checkout_session(request).bill_to_user_address(address)
        return Response({'billing': {'address': _user_address_payload(address)}})


class GuestOrderLookupAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        order_number = str(request.data.get('order_number', '')).strip()
        email = str(request.data.get('email', '')).strip().lower()
        Order = apps.get_model('order', 'Order')
        order = get_object_or_404(Order, number=order_number)
        order_email = (getattr(order, 'guest_email', '') or getattr(order.user, 'email', '') or '').lower()
        if order_email != email:
            return Response(status=status.HTTP_404_NOT_FOUND)
        lookup_hash = signing.dumps({'order_number': order.number, 'email': email}, salt='guest-order-lookup')
        return Response({'order_number': order.number, 'hash': lookup_hash})


class GuestOrderDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, order_number: str, lookup_hash: str):
        try:
            payload = signing.loads(lookup_hash, salt='guest-order-lookup', max_age=60 * 60 * 24 * 30)
        except signing.BadSignature:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if payload.get('order_number') != order_number:
            return Response(status=status.HTTP_404_NOT_FOUND)
        Order = apps.get_model('order', 'Order')
        order = get_object_or_404(Order, number=order_number)
        return Response({'order': OrderSummarySerializer(order).data})


class AccountOrderLineDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number: str, line_id: int):
        OrderLine = apps.get_model('order', 'Line')
        line = get_object_or_404(OrderLine.objects.select_related('order', 'product'), id=line_id, order__number=order_number, order__user=request.user)
        return Response(
            {
                'line': {
                    'id': line.id,
                    'order_number': line.order.number,
                    'status': line.status,
                    'quantity': line.quantity,
                    'title': line.title,
                    'upc': line.upc,
                    'line_price_before_discounts': _money_payload(line.line_price_before_discounts_incl_tax),
                    'line_price': _money_payload(line.line_price_incl_tax),
                    'currency': line.order.currency,
                    'product': serialize_product_card(line.product, display_currency=resolve_display_currency(request)) if line.product else None,
                }
            }
        )


class AccountEmailCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        emails = EmailNotification.objects.filter(recipient__iexact=request.user.email).exclude(metadata__archived=True)[:100]
        return Response({'results': [_email_payload(email) for email in emails]})


class AccountEmailDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, email_id: int):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        email = get_object_or_404(EmailNotification, id=email_id, recipient__iexact=request.user.email)
        return Response({'email': _email_payload(email)})


def _email_payload(email) -> dict:
    return {
        'id': email.id,
        'event_type': email.event_type,
        'status': email.status,
        'recipient': email.recipient,
        'subject': email.subject,
        'metadata': email.metadata,
        'read': bool((email.metadata or {}).get('read')),
        'archived': bool((email.metadata or {}).get('archived')),
        'error_message': email.error_message,
        'sent_at': email.sent_at.isoformat() if email.sent_at else None,
        'created_at': email.created_at.isoformat(),
    }


class AccountNotificationCollectionAPIView(AccountEmailCollectionAPIView):
    pass


class AccountNotificationArchiveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        emails = EmailNotification.objects.filter(recipient__iexact=request.user.email, metadata__archived=True)[:100]
        return Response({'results': [_email_payload(email) for email in emails]})


class AccountNotificationDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, notification_id: int):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        notification = get_object_or_404(EmailNotification, id=notification_id, recipient__iexact=request.user.email)
        return Response({'notification': _email_payload(notification)})


class AccountNotificationStateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id: int, action: str):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        notification = get_object_or_404(EmailNotification, id=notification_id, recipient__iexact=request.user.email)
        notification.metadata = {**notification.metadata, action: True}
        notification.save(update_fields=['metadata', 'updated_at'])
        return Response({'notification': _email_payload(notification)})


class AccountNotificationReadAllAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        EmailNotification = apps.get_model('notifications', 'EmailNotification')
        for notification in EmailNotification.objects.filter(recipient__iexact=request.user.email):
            notification.metadata = {**notification.metadata, 'read': True}
            notification.save(update_fields=['metadata', 'updated_at'])
        return Response({'detail': 'Notifications marked as read.'})


def _product_alert_payload(alert, display_currency: str | None = None) -> dict:
    payload = {
        'id': alert.id,
        'product_id': alert.product_id,
        'email': alert.email,
        'status': alert.status,
        'key': alert.key,
        'date_created': alert.date_created.isoformat(),
        'date_confirmed': alert.date_confirmed.isoformat() if alert.date_confirmed else None,
        'date_cancelled': alert.date_cancelled.isoformat() if alert.date_cancelled else None,
    }
    if getattr(alert, 'product', None):
        payload['product'] = serialize_product_card(alert.product, display_currency=display_currency)
    return payload


class AccountProductAlertCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ProductAlert = apps.get_model('customer', 'ProductAlert')
        display_currency = resolve_display_currency(request)
        alerts = (
            ProductAlert.objects.filter(user=request.user)
            .select_related('product')
            .prefetch_related('product__stockrecords', 'product__images', 'product__reviews')
            .order_by('-date_created')
        )
        return Response({'results': [_product_alert_payload(alert, display_currency=display_currency) for alert in alerts]})


class ProductAlertCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, product_id: int):
        Product = apps.get_model('catalogue', 'Product')
        ProductAlert = apps.get_model('customer', 'ProductAlert')
        product = get_object_or_404(Product, id=product_id, is_public=True)
        email = request.data.get('email') or (request.user.email if request.user.is_authenticated else '')
        if not email:
            raise serializers.ValidationError({'email': 'Email is required.'})
        alert, _ = ProductAlert.objects.get_or_create(
            product=product,
            email=email,
            defaults={'user': request.user if request.user.is_authenticated else None},
        )
        return Response({'alert': _product_alert_payload(alert, display_currency=resolve_display_currency(request))}, status=status.HTTP_201_CREATED)


class ProductAlertConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, key: str):
        ProductAlert = apps.get_model('customer', 'ProductAlert')
        alert = get_object_or_404(ProductAlert, key=key)
        if alert.can_be_confirmed:
            alert.confirm()
        return Response({'alert': _product_alert_payload(alert, display_currency=resolve_display_currency(request))})


class ProductAlertCancelAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, key: str):
        ProductAlert = apps.get_model('customer', 'ProductAlert')
        alert = get_object_or_404(ProductAlert, key=key)
        if alert.can_be_cancelled:
            alert.cancel()
        return Response({'alert': _product_alert_payload(alert, display_currency=resolve_display_currency(request))})


class AccountProductAlertDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, alert_id: int):
        ProductAlert = apps.get_model('customer', 'ProductAlert')
        alert = get_object_or_404(ProductAlert, id=alert_id, user=request.user)
        if alert.can_be_cancelled:
            alert.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_password_reset'

    def post(self, request):
        email = str(request.data.get('email', '')).strip()
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        payload = {'detail': 'If that email exists, password reset instructions will be sent.'}
        if user:
            if not user.is_active:
                return Response({
                    'detail': 'This account is deactivated. Request reactivation before resetting the password.',
                    'account_inactive': True,
                })
            queue_password_reset_email(user)
        return Response(payload)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_password_reset'

    def post(self, request):
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        password = request.data.get('new_password', '')
        password_confirm = request.data.get('new_password_confirm', '')
        if password != password_confirm:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
        except Exception as exc:
            raise serializers.ValidationError({'uid': 'Invalid reset link.'}) from exc
        if not user_id:
            raise serializers.ValidationError({'uid': 'Invalid reset link.'})
        user = get_object_or_404(get_user_model(), pk=user_id)
        if not user.is_active:
            raise serializers.ValidationError({
                'token': 'This account is deactivated. Request reactivation before resetting the password.'
            })
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({
                'token': 'Invalid or expired reset token. Password reset links expire in 30 minutes.'
            })
        password_validation.validate_password(password, user=user)
        user.set_password(password)
        user.save(update_fields=['password'])
        queue_password_changed_email(user)
        return Response({'detail': 'Password reset successfully.'})


class AccountDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            raise serializers.ValidationError({'password': 'Password is incorrect.'})
        request.user.is_active = False
        request.user.save(update_fields=['is_active'])
        return Response({'detail': 'Account deactivated. Contact support if you need it reactivated.'})


class RecentlyViewedAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        Product = apps.get_model('catalogue', 'Product')
        product_ids = request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
        products = {product.id: product for product in Product.objects.filter(id__in=product_ids)}
        return Response(
            {
                'results': [
                    serialize_product_card(products[product_id], display_currency=resolve_display_currency(request))
                    for product_id in product_ids
                    if product_id in products
                ]
            }
        )


class ProductViewedAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, product_id: int):
        get_object_or_404(public_product_queryset(), id=product_id)
        product_ids = [pid for pid in request.session.get(RECENTLY_VIEWED_SESSION_KEY, []) if pid != product_id]
        request.session[RECENTLY_VIEWED_SESSION_KEY] = [product_id, *product_ids][:24]
        request.session.modified = True
        return Response({'product_id': product_id})


class StorefrontAnalyticsEventAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_event = str(request.data.get('event_type') or request.data.get('event') or '').strip()
        if not raw_event:
            raise serializers.ValidationError({'event_type': 'Event type is required.'})
        event_type = raw_event if raw_event.startswith('storefront.') else f'storefront.{raw_event}'
        if event_type not in ALLOWED_STOREFRONT_ANALYTICS_EVENTS:
            raise serializers.ValidationError({'event_type': 'Unsupported storefront analytics event.'})

        metadata = request.data.get('metadata') or {}
        if not isinstance(metadata, dict):
            raise serializers.ValidationError({'metadata': 'Metadata must be an object.'})
        metadata = _analytics_metadata(metadata)
        product_id = metadata.get('product_id')
        target = None
        if product_id:
            target = public_product_queryset().filter(id=product_id).first()

        record_audit_event(
            event_type=event_type,
            request=request,
            target=target,
            message='Storefront analytics event.',
            metadata=metadata,
        )
        return Response({'detail': 'Event recorded.'}, status=status.HTTP_201_CREATED)


def _analytics_metadata(metadata: dict) -> dict:
    allowed_keys = {
        'path',
        'title',
        'referrer',
        'search',
        'product_id',
        'product_title',
        'quantity',
        'line_id',
        'saved_line_id',
        'voucher_id',
        'code',
        'order_number',
        'currency',
        'total',
        'source',
    }
    clean = {}
    for key, value in metadata.items():
        if key not in allowed_keys:
            continue
        if isinstance(value, str):
            clean[key] = value[:255]
        elif isinstance(value, (int, float, bool)) or value is None:
            clean[key] = value
    return clean


class ProductReviewDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id: int, review_id: int):
        product = get_object_or_404(public_product_queryset(), id=product_id)
        Review = get_review_model()
        review = get_object_or_404(Review.objects.select_related('user', 'product'), id=review_id, product=product, status=Review.APPROVED)
        return Response({'review': review_payload(review, request_user=request.user)})


class ProductReviewVoteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id: int, review_id: int):
        product = get_object_or_404(public_product_queryset(), id=product_id)
        Review = get_review_model()
        review = get_object_or_404(Review.objects.select_related('user', 'product'), id=review_id, product=product, status=Review.APPROVED)
        raw_delta = request.data.get('delta', request.data.get('vote', 'up'))
        delta = -1 if str(raw_delta).lower() in {'-1', 'down', 'no', 'false'} else 1
        Vote = apps.get_model('reviews', 'Vote')
        vote = Vote(review=review, user=request.user, delta=delta)
        try:
            vote.full_clean()
            vote.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'vote': exc.messages}) from exc
        review.refresh_from_db()
        return Response({'review': review_payload(review, request_user=request.user)}, status=status.HTTP_201_CREATED)


class SearchFacetAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        Product = apps.get_model('catalogue', 'Product')
        products = Product.objects.filter(is_public=True).exclude(structure='parent')
        categories = apps.get_model('catalogue', 'Category').objects.filter(product__in=products).distinct()[:50]
        brands = (
            products.filter(attribute_values__attribute__code='brand')
            .values_list('attribute_values__value_text', flat=True)
            .distinct()[:50]
        )
        return Response(
            {
                'facets': {
                    'categories': [{'name': category.name, 'slug': category.slug} for category in categories],
                    'price_ranges': [
                        {'label': 'Under 100', 'min': None, 'max': 100},
                        {'label': '100 to 500', 'min': 100, 'max': 500},
                        {'label': '500 to 1000', 'min': 500, 'max': 1000},
                        {'label': '1000+', 'min': 1000, 'max': None},
                    ],
                    'brands': [{'name': brand} for brand in brands if brand],
                    'availability': [{'value': True, 'label': 'In stock'}],
                }
            }
        )


class BillingStateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        fields = get_checkout_session(request).new_billing_address_fields()
        return Response({'billing': {'address': fields or None}})


class BillingAddressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        country = data.pop('country_code')
        get_checkout_session(request).bill_to_new_address({**data, 'country': country})
        return Response({'billing': {'address': request.data}})


class AccountPreferenceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        return Response(
            {
                'preferences': {
                    'receive_order_updates': profile.receive_order_updates,
                    'receive_marketing_emails': profile.receive_marketing_emails,
                    'two_factor_email_enabled': profile.two_factor_email_enabled,
                    'email_verified': profile.email_verified_at is not None,
                    'email_verified_at': profile.email_verified_at.isoformat() if profile.email_verified_at else None,
                    'preferred_currency': profile.preferred_currency,
                    'country_code': profile.country_code,
                    'phone': profile.phone,
                    'company': profile.company,
                }
            }
        )

    def patch(self, request):
        CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        allowed_fields = {
            'receive_order_updates',
            'receive_marketing_emails',
            'two_factor_email_enabled',
            'preferred_currency',
            'country_code',
            'phone',
            'company',
        }
        update_fields = []
        for field in allowed_fields:
            if field in request.data:
                value = request.data[field]
                if field == 'two_factor_email_enabled' and value and profile.email_verified_at is None:
                    raise serializers.ValidationError({'two_factor_email_enabled': 'Verify your email before enabling email 2FA.'})
                if field == 'country_code':
                    value = normalize_country_code(value)
                    if value and currency_for_country(value) is None:
                        raise serializers.ValidationError({'country_code': 'Unsupported country code.'})
                elif field == 'preferred_currency':
                    value = normalize_currency_code(value)
                    if value and not is_supported_currency(value):
                        raise serializers.ValidationError({'preferred_currency': 'Unsupported currency.'})
                elif field in {'phone', 'company'} and isinstance(value, str):
                    value = value.strip()
                setattr(profile, field, value)
                update_fields.append(field)
        if update_fields:
            update_fields.append('updated_at')
            profile.save(update_fields=update_fields)
        return self.get(request)
