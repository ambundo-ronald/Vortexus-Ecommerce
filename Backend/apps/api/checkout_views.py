import logging

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from oscar.apps.order.utils import OrderCreator, OrderNumberGenerator
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.services import send_order_confirmation_email
from apps.inventory.services import (
    InventoryReservationError,
    prepare_basket_for_order_submission,
    release_basket_line_reservation,
    sync_basket_line_reservation,
)
from apps.payments.services import link_payment_to_order, payment_requires_prepayment
from apps.marketplace.orders import ensure_supplier_order_groups

from .checkout_serializers import (
    BasketItemCreateSerializer,
    BasketLineUpdateSerializer,
    ShippingAddressSerializer,
    ShippingMethodSelectionSerializer,
)
from .checkout_utils import (
    build_checkout_payload,
    clear_selected_shipping_method,
    get_checkout_session,
    get_shipping_address,
    get_shipping_methods,
)
from .order_serializers import OrderPlacementSerializer, OrderSummarySerializer, build_order_prices

logger = logging.getLogger(__name__)


class BasketAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'basket': build_checkout_payload(request)['basket']})


class BasketItemCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = BasketItemCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        line, _ = request.basket.add_product(
            serializer.validated_data['product'],
            quantity=serializer.validated_data['quantity'],
        )
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
            payment_session = get_object_or_404(PaymentSession, reference=payment_reference)
            if payment_session.order_id:
                raise serializers.ValidationError({'payment_reference': 'This payment has already been used for an order.'})
            if payment_session.basket_id and payment_session.basket_id != basket.id:
                raise serializers.ValidationError({'payment_reference': 'This payment session does not belong to the current basket.'})
            if request.user.is_authenticated and payment_session.user_id and payment_session.user_id != request.user.id:
                raise serializers.ValidationError({'payment_reference': 'This payment session belongs to a different account.'})
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

        extra_order_fields = {'guest_email': guest_email} if guest_email else {}
        try:
            order = OrderCreator().place_order(
                basket=basket,
                total=pricing['order_total'],
                shipping_method=shipping_method,
                shipping_charge=pricing['shipping_price'],
                user=request.user if request.user.is_authenticated else None,
                shipping_address=shipping_address,
                order_number=order_number,
                status=getattr(settings, 'OSCAR_INITIAL_ORDER_STATUS', 'Pending'),
                request=request,
                **extra_order_fields,
            )
        except ValueError as exc:
            raise serializers.ValidationError({'order': str(exc)}) from exc
        link_payment_to_order(payment_session, order)
        ensure_supplier_order_groups(order)
        basket.submit()
        checkout_session.flush()

        send_order_confirmation_email(order)
        logger.info('Order placed successfully: number=%s user=%s', order.number, getattr(request.user, 'id', None))

        return Response(
            {
                'detail': 'Order placed successfully.',
                'order': OrderSummarySerializer(order).data,
                'payment': {'reference': payment_session.reference, 'status': payment_session.status, 'method': payment_session.method},
                'taxes': pricing['tax_breakdown'],
            },
            status=status.HTTP_201_CREATED,
        )
