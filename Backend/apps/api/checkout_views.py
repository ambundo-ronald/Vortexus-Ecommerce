import logging
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from oscar.apps.order.utils import OrderCreator, OrderNumberGenerator
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.common.async_utils import dispatch_background_task
from apps.integrations.tasks import export_order_to_erpnext, sync_customer_to_erpnext
from apps.notifications.services import queue_order_confirmation_email, queue_password_reset_email
from apps.inventory.services import (
    InventoryReservationError,
    prepare_basket_for_order_submission,
    release_basket_line_reservation,
    sync_basket_line_reservation,
)
from apps.payments.services import link_payment_to_order, payment_requires_prepayment, serialize_payment_session
from apps.marketplace.orders import ensure_supplier_order_groups
from apps.accounts.delivery_locations import (
    get_session_location,
    upsert_user_address_location,
    store_session_location,
    upsert_shipping_address_location,
)

from .checkout_serializers import (
    BasketItemCreateSerializer,
    BasketLineUpdateSerializer,
    ShippingAddressSerializer,
    ShippingMethodSelectionSerializer,
)
from .checkout_utils import (
    build_checkout_payload,
    clear_selected_shipping_method,
    ensure_basket_default_currency,
    get_checkout_session,
    get_selected_shipping_method,
    get_shipping_address,
    get_shipping_methods,
)
from .order_serializers import OrderPlacementSerializer, OrderSummarySerializer, build_order_prices

logger = logging.getLogger(__name__)


def _generate_customer_username(email: str) -> str:
    User = get_user_model()
    base = slugify(email.split('@', 1)[0]).replace('-', '_')[:120] or 'customer'
    candidate = base
    suffix = 1
    while User.objects.filter(username__iexact=candidate).exists():
        suffix += 1
        candidate = f'{base[:140]}_{suffix}'
    return candidate[:150]


def _create_or_link_guest_customer(*, guest_email: str, shipping_address=None, payment_session=None) -> tuple[object | None, dict]:
    email = (guest_email or '').strip().lower()
    account_setup = {
        'required': False,
        'email': email,
        'created': False,
        'existing_account': False,
        'setup_email_sent': False,
    }
    if not email:
        return None, account_setup

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if user:
        account_setup['existing_account'] = True
    else:
        user = User(
            username=_generate_customer_username(email),
            email=email,
            first_name=(getattr(shipping_address, 'first_name', '') or '').strip(),
            last_name=(getattr(shipping_address, 'last_name', '') or '').strip(),
            is_active=True,
        )
        user.set_unusable_password()
        user.save()
        account_setup['created'] = True

    CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    phone = str(getattr(shipping_address, 'phone_number', '') or '').strip()
    dirty_fields = []
    if phone and not profile.phone:
        profile.phone = phone
        dirty_fields.append('phone')
    if not profile.receive_order_updates:
        profile.receive_order_updates = True
        dirty_fields.append('receive_order_updates')
    if dirty_fields:
        profile.save(update_fields=[*dirty_fields, 'updated_at'])

    if payment_session and not payment_session.user_id:
        payment_session.user = user
        payment_session.save(update_fields=['user', 'updated_at'])

    if user.is_active and account_setup['created']:
        queue_password_reset_email(user)
        account_setup['setup_email_sent'] = True
    account_setup['required'] = True
    return user, account_setup


def _save_shipping_address_to_book(request, serializer: ShippingAddressSerializer):
    if not request.user.is_authenticated:
        return None

    UserAddress = apps.get_model('address', 'UserAddress')
    session_fields = serializer.to_session_fields()
    country = serializer.context['country']
    data = serializer.validated_data
    title = (
        data.get('location_label')
        or data.get('line1')
        or data.get('line4')
        or 'Delivery address'
    )[:64]
    defaults = {
        'title': title,
        'first_name': session_fields['first_name'],
        'last_name': session_fields['last_name'],
        'line1': session_fields['line1'],
        'line2': session_fields.get('line2', ''),
        'line3': session_fields.get('line3', ''),
        'line4': session_fields['line4'],
        'state': session_fields.get('state', ''),
        'postcode': session_fields.get('postcode', ''),
        'country': country,
        'phone_number': session_fields.get('phone_number', ''),
        'notes': session_fields.get('notes', ''),
        'user': request.user,
    }
    lookup = {
        'user': request.user,
        'line1': defaults['line1'],
        'line2': defaults['line2'],
        'line3': defaults['line3'],
        'line4': defaults['line4'],
        'postcode': defaults['postcode'],
        'country': country,
        'phone_number': defaults['phone_number'],
    }
    address = UserAddress.objects.filter(**lookup).order_by('-date_created').first()
    if address:
        for field, value in defaults.items():
            setattr(address, field, value)
        if not request.user.addresses.filter(is_default_for_shipping=True).exclude(id=address.id).exists():
            address.is_default_for_shipping = True
        address.save()
    else:
        defaults['is_default_for_shipping'] = not request.user.addresses.filter(is_default_for_shipping=True).exists()
        address = UserAddress.objects.create(**defaults)

    location_payload = serializer.location_payload()
    if location_payload:
        upsert_user_address_location(address, location_payload)
    return address


def _nominatim_place_payload(item: dict) -> dict:
    address = item.get('address') or {}
    importance = item.get('importance')
    try:
        confidence = max(0.0, min(1.0, float(importance or 0)))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        'place_id': str(item.get('place_id') or item.get('osm_id') or ''),
        'provider': 'nominatim',
        'label': item.get('display_name') or item.get('name') or '',
        'formatted_address': item.get('display_name') or '',
        'latitude': item.get('lat'),
        'longitude': item.get('lon'),
        'confidence': confidence,
        'address': {
            'road': address.get('road') or '',
            'suburb': address.get('suburb') or address.get('neighbourhood') or '',
            'city': address.get('city') or address.get('town') or address.get('village') or address.get('county') or '',
            'state': address.get('state') or address.get('county') or '',
            'postcode': address.get('postcode') or '',
            'country_code': str(address.get('country_code') or '').upper(),
        },
    }


class DeliveryPlaceSearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = str(request.query_params.get('q') or '').strip()
        if len(query) < 3:
            raise serializers.ValidationError({'q': 'Enter at least 3 characters to search delivery places.'})

        country_code = str(request.query_params.get('country_code') or 'KE').strip().lower()[:2]
        limit = min(max(int(request.query_params.get('limit', 6) or 6), 1), 8)
        cache_key = f'delivery-place-search:{country_code}:{limit}:{query.lower()}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response({'results': cached, 'provider': 'nominatim', 'cached': True})

        params = {
            'format': 'jsonv2',
            'q': query,
            'limit': str(limit),
            'addressdetails': '1',
        }
        if country_code:
            params['countrycodes'] = country_code

        url = f'https://nominatim.openstreetmap.org/search?{urlencode(params)}'
        user_agent = getattr(settings, 'DELIVERY_GEOCODING_USER_AGENT', 'Reesolmart delivery search')
        request_obj = Request(url, headers={'Accept': 'application/json', 'User-Agent': user_agent})
        try:
            with urlopen(request_obj, timeout=int(getattr(settings, 'DELIVERY_GEOCODING_TIMEOUT_SECONDS', 8))) as response:
                raw_payload = response.read().decode('utf-8')
        except (HTTPError, URLError, TimeoutError) as exc:
            logger.warning('Delivery place search failed: %s', exc)
            return Response(
                {
                    'error': {
                        'code': 'place_search_unavailable',
                        'detail': 'Place search is not available right now. Try again or pin your current location.',
                        'status': 503,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            payload = []

        results = [_nominatim_place_payload(item) for item in payload if item.get('lat') and item.get('lon')]
        cache.set(cache_key, results, int(getattr(settings, 'DELIVERY_GEOCODING_CACHE_SECONDS', 60 * 60 * 24)))
        return Response({'results': results, 'provider': 'nominatim', 'cached': False})


def _order_payment_payload(order):
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    payment_session = (
        PaymentSession.objects.select_related('order')
        .filter(order=order)
        .order_by('-paid_at', '-updated_at', '-created_at')
        .first()
    )
    return serialize_payment_session(payment_session) if payment_session else None


def _basket_value_error_message(exc: ValueError) -> str:
    message = str(exc)
    if 'same currency' in message and 'Proposed line has currency' in message:
        return (
            'This product uses a different currency from the items already in your cart. '
            'Please checkout or clear the current cart first, then add this product.'
        )
    return message


class BasketAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ensure_basket_default_currency(request.basket)
        return Response({'basket': build_checkout_payload(request)['basket']})


def _add_product_with_stockrecord(basket, product, stockrecord, quantity, options):
    stock_info = basket.strategy.fetch_for_product(product)
    price_currency = basket.currency
    if price_currency and stock_info.price.currency != price_currency:
        raise ValueError(
            (
                'Basket lines must all have the same currency. Proposed '
                'line has currency %s, while basket has currency %s'
            )
            % (stock_info.price.currency, price_currency)
        )
    line_ref = basket._create_line_reference(product, stockrecord, options)
    defaults = {
        'quantity': quantity,
        'price_excl_tax': stock_info.price.excl_tax,
        'price_currency': stock_info.price.currency,
        'tax_code': stock_info.price.tax_code,
        'stockrecord': stockrecord,
    }
    if stock_info.price.is_tax_known:
        defaults['price_incl_tax'] = stock_info.price.incl_tax
    line, created = basket.lines.get_or_create(
        line_reference=line_ref,
        product=product,
        stockrecord=stockrecord,
        defaults=defaults,
    )
    if created:
        for option_dict in options:
            line.attributes.create(option=option_dict['option'], value=option_dict['value'])
    else:
        line.quantity = max(0, line.quantity + quantity)
        line.save()
    basket.reset_offer_applications()
    return line, created


class BasketItemCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        if request.basket.pk is None:
            request.basket.save()
        serializer = BasketItemCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            line, _ = _add_product_with_stockrecord(
                request.basket,
                serializer.validated_data['product'],
                serializer.validated_data['stockrecord'],
                serializer.validated_data['quantity'],
                serializer.validated_data.get('options') or [],
            )
        except ValueError as exc:
            raise serializers.ValidationError({'basket': _basket_value_error_message(exc)}) from exc
        try:
            sync_basket_line_reservation(line)
        except InventoryReservationError as exc:
            raise serializers.ValidationError({'quantity': str(exc)}) from exc
        request.basket._lines = None
        return Response(build_checkout_payload(request), status=status.HTTP_201_CREATED)


class BasketLineDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def patch(self, request, line_id: int):
        line = get_object_or_404(request.basket.lines.select_related('product', 'stockrecord'), id=line_id)
        serializer = BasketLineUpdateSerializer(data=request.data, context={'request': request, 'line': line})
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['quantity']
        if quantity == 0:
            release_basket_line_reservation(line)
            line.delete()
        else:
            line.quantity = quantity
            line.save()
            try:
                sync_basket_line_reservation(line)
            except InventoryReservationError as exc:
                raise serializers.ValidationError({'quantity': str(exc)}) from exc

        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request))

    @transaction.atomic
    def delete(self, request, line_id: int):
        line = get_object_or_404(request.basket.lines.all(), id=line_id)
        release_basket_line_reservation(line)
        line.delete()
        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request), status=status.HTTP_200_OK)


class ShippingStateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(build_checkout_payload(request))


class ShippingAddressAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request):
        serializer = ShippingAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        checkout_session = get_checkout_session(request)
        checkout_session.ship_to_new_address(serializer.to_session_fields())
        store_session_location(request, serializer.location_payload())
        _save_shipping_address_to_book(request, serializer)
        clear_selected_shipping_method(request)
        return Response(build_checkout_payload(request))


class ShippingMethodSelectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ShippingMethodSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_address = get_shipping_address(request, request.basket)
        methods = get_shipping_methods(request, request.basket, shipping_address=shipping_address)

        method_code = serializer.validated_data['method_code']
        method_codes = {method.code for method in methods}
        if method_code not in method_codes:
            return Response(
                {
                    'error': {
                        'code': 'invalid_shipping_method',
                        'detail': 'The selected shipping method is not available for this basket.',
                        'status': 400,
                        'errors': {'method_code': ['The selected shipping method is not available.']},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        get_checkout_session(request).use_shipping_method(method_code)
        return Response(build_checkout_payload(request))


class CheckoutPreviewAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        basket = request.basket
        if basket.is_empty:
            raise serializers.ValidationError({'basket': 'Your basket is empty.'})
        shipping_address = get_shipping_address(request, basket)
        shipping_method = get_selected_shipping_method(request, basket, shipping_address=shipping_address)
        payload = build_checkout_payload(request)
        preview = {
            'ready': True,
            'missing': [],
            'basket': payload['basket'],
            'shipping': payload.get('shipping'),
            'billing': payload.get('billing'),
        }
        if basket.is_shipping_required() and not shipping_address:
            preview['ready'] = False
            preview['missing'].append('shipping_address')
        if basket.is_shipping_required() and not shipping_method:
            preview['ready'] = False
            preview['missing'].append('shipping_method')
        if preview['ready']:
            pricing = build_order_prices(basket, shipping_address, shipping_method)
            preview['totals'] = {
                'shipping': float(pricing['shipping_price'].incl_tax),
                'order_total': float(pricing['order_total'].incl_tax),
                'currency': pricing['order_total'].currency,
                'taxes': pricing['tax_breakdown'],
            }
        return Response({'preview': preview})


class CheckoutThankYouAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        checkout_session = get_checkout_session(request)
        session_order_number = checkout_session.get_order_number()
        order_number = request.query_params.get('order_number') or session_order_number
        if not order_number:
            raise serializers.ValidationError({'order_number': 'Order number is required.'})
        Order = apps.get_model('order', 'Order')
        queryset = Order.objects.select_related('user', 'shipping_address')
        if request.user.is_authenticated:
            order = get_object_or_404(queryset, number=order_number, user=request.user)
        else:
            if not session_order_number or str(order_number) != str(session_order_number):
                raise serializers.ValidationError({'order_number': 'Order confirmation is only available for this checkout session.'})
            order = get_object_or_404(queryset, number=order_number)
        return Response(
            {
                'detail': 'Order placed successfully.',
                'order': OrderSummarySerializer(order).data,
                'payment': _order_payment_payload(order),
            }
        )


class OrderPlacementAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = OrderPlacementSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        PaymentSession = apps.get_model('payments', 'PaymentSession')
        basket = request.basket
        shipping_address = serializer.validated_data['shipping_address']
        shipping_method = serializer.validated_data['shipping_method']
        guest_email = serializer.validated_data['guest_email']
        payment_reference = serializer.validated_data['payment_reference']
        checkout_session = get_checkout_session(request)

        if guest_email:
            checkout_session.set_guest_email(guest_email)

        pricing = build_order_prices(basket, shipping_address, shipping_method)
        payment_session = None
        if payment_reference:
            payment_session = get_object_or_404(
                PaymentSession.objects.select_for_update(of=('self',)).select_related('user'),
                reference=payment_reference,
            )
            if request.user.is_authenticated and payment_session.user_id and payment_session.user_id != request.user.id:
                raise serializers.ValidationError({'payment_reference': 'This payment session belongs to a different account.'})
            if payment_session.order_id:
                linked_order = get_object_or_404(apps.get_model('order', 'Order'), pk=payment_session.order_id)
                if request.user.is_authenticated and linked_order.user_id and linked_order.user_id != request.user.id:
                    raise serializers.ValidationError({'payment_reference': 'This payment is linked to a different account.'})
                checkout_session.set_order_number(linked_order.number)
                return Response(
                    {
                        'detail': 'Order already placed for this payment.',
                        'order': OrderSummarySerializer(linked_order).data,
                        'payment': serialize_payment_session(payment_session),
                        'taxes': {},
                    },
                    status=status.HTTP_200_OK,
                )
            if payment_session.basket_id and payment_session.basket_id != basket.id:
                raise serializers.ValidationError({'payment_reference': 'This payment session does not belong to the current basket.'})
            if payment_session.currency != pricing['order_total'].currency:
                raise serializers.ValidationError({'payment_reference': 'Payment currency does not match the current order currency.'})
            if payment_session.amount != pricing['order_total'].incl_tax:
                raise serializers.ValidationError({'payment_reference': 'Payment amount no longer matches the current order total.'})
            expected_shipping_code = shipping_method.code if shipping_method else ''
            if (payment_session.metadata or {}).get('shipping_method', '') != expected_shipping_code:
                raise serializers.ValidationError({'payment_reference': 'Shipping method changed after payment initialization.'})
            if (payment_session.metadata or {}).get('country_code', '') != pricing['tax_breakdown']['country_code']:
                raise serializers.ValidationError({'payment_reference': 'Shipping destination changed after payment initialization.'})
            if payment_requires_prepayment(payment_session.method) and payment_session.status not in {'authorized', 'paid'}:
                raise serializers.ValidationError({'payment_reference': 'Payment must be completed before placing the order.'})
        else:
            raise serializers.ValidationError({'payment_reference': 'Payment reference is required before placing the order.'})

        try:
            prepare_basket_for_order_submission(basket)
        except InventoryReservationError as exc:
            raise serializers.ValidationError({'basket': str(exc)}) from exc

        order_number = OrderNumberGenerator().order_number(basket)
        checkout_session.set_order_number(order_number)
        checkout_session.set_submitted_basket(basket)

        if shipping_address and shipping_address.pk is None:
            shipping_address.save()
        delivery_location = get_session_location(request)

        order_user = request.user if request.user.is_authenticated else None
        account_setup = {
            'required': False,
            'email': guest_email,
            'created': False,
            'existing_account': False,
            'setup_email_sent': False,
        }
        if not order_user and guest_email:
            order_user, account_setup = _create_or_link_guest_customer(
                guest_email=guest_email,
                shipping_address=shipping_address,
                payment_session=payment_session,
            )

        extra_order_fields = {'guest_email': guest_email} if guest_email else {}
        try:
            order = OrderCreator().place_order(
                basket=basket,
                total=pricing['order_total'],
                shipping_method=shipping_method,
                shipping_charge=pricing['shipping_price'],
                user=order_user,
                shipping_address=shipping_address,
                order_number=order_number,
                status=getattr(settings, 'OSCAR_INITIAL_ORDER_STATUS', 'Pending'),
                request=request,
                **extra_order_fields,
            )
        except ValueError as exc:
            raise serializers.ValidationError({'order': str(exc)}) from exc
        upsert_shipping_address_location(order.shipping_address, delivery_location)
        link_payment_to_order(payment_session, order)
        ensure_supplier_order_groups(order)
        _post_order_accounting(order, request.user)
        basket.submit()
        checkout_session.flush()

        queue_order_confirmation_email(order)
        dispatch_background_task(
            export_order_to_erpnext,
            run_kwargs={'order_number': order.number},
            async_kwargs={'order_number': order.number},
        )
        if account_setup.get('created') and order_user:
            dispatch_background_task(
                sync_customer_to_erpnext,
                run_kwargs={'user_id': order_user.id},
                async_kwargs={'user_id': order_user.id},
            )
        logger.info('Order placed successfully: number=%s user=%s', order.number, getattr(request.user, 'id', None))
        record_audit_event(
            event_type='orders.placed',
            request=request,
            actor=request.user if request.user.is_authenticated else order_user,
            target=order,
            message='Order placed successfully.',
            metadata={
                'order_number': order.number,
                'payment_reference': payment_session.reference,
                'payment_method': payment_session.method,
                'guest_checkout': bool(guest_email and not request.user.is_authenticated),
                'customer_account_created': account_setup.get('created', False),
                'customer_account_existing': account_setup.get('existing_account', False),
            },
        )

        return Response(
            {
                'detail': 'Order placed successfully.',
                'order': OrderSummarySerializer(order).data,
                'payment': serialize_payment_session(payment_session),
                'account_setup': account_setup,
                'taxes': pricing['tax_breakdown'],
            },
            status=status.HTTP_201_CREATED,
        )


def _post_order_accounting(order, user=None) -> None:
    try:
        from apps.accounting.services import post_sales_order

        post_sales_order(order, user=user)
    except Exception:
        logger.exception('Failed to post sales order accounting for %s', getattr(order, 'number', ''))
