from decimal import Decimal

from rest_framework import serializers
from django.conf import settings

from apps.payments.services import get_payment_method

from .checkout_utils import get_selected_shipping_method, get_shipping_address
from .order_serializers import build_order_prices

MPESA_TRANSACTION_LIMIT_KES = Decimal('150000.00')


class PaymentMethodSerializer(serializers.Serializer):
    def to_representation(self, method):
        return method


class PaymentInitializationSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[(method['code'], method['name']) for method in settings.PAYMENT_METHODS])
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=40)
    payer_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context['request']
        basket = request.basket
        shipping_address = get_shipping_address(request, basket)
        shipping_method = get_selected_shipping_method(request, basket, shipping_address=shipping_address)
        method = get_payment_method(attrs['method'])

        if basket.is_empty:
            raise serializers.ValidationError({'basket': 'Your basket is empty.'})
        if method is None:
            raise serializers.ValidationError({'method': 'This payment method is not currently available.'})
        if basket.is_shipping_required() and not shipping_address:
            raise serializers.ValidationError({'shipping_address': 'Shipping address is required before payment initialization.'})
        if basket.is_shipping_required() and not shipping_method:
            raise serializers.ValidationError({'shipping_method': 'Shipping method is required before payment initialization.'})

        if method.get('requires_phone') and not (attrs.get('phone_number') or '').strip():
            raise serializers.ValidationError({'phone_number': f"{method['name']} requires a phone number."})

        pricing = build_order_prices(basket, shipping_address, shipping_method)
        order_total = pricing['order_total']
        if order_total.currency == 'KES' and order_total.incl_tax > MPESA_TRANSACTION_LIMIT_KES:
            raise serializers.ValidationError({
                'basket': (
                    'Orders above Ksh 150,000 cannot continue to payment because M-Pesa allows '
                    'a maximum of Ksh 150,000 per transaction. Request a quotation instead.'
                )
            })

        attrs['shipping_address'] = shipping_address
        attrs['shipping_method'] = shipping_method
        attrs['pricing'] = pricing
        attrs['payer_email'] = (attrs.get('payer_email') or '').strip().lower()
        attrs['phone_number'] = (attrs.get('phone_number') or '').strip()
        return attrs


class PaymentConfirmationSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    external_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)


class MpesaInitializationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=40)
    payer_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        data = PaymentInitializationSerializer(
            data={
                'method': 'mpesa',
                'phone_number': attrs.get('phone_number', ''),
                'payer_email': attrs.get('payer_email', ''),
            },
            context=self.context,
        )
        data.is_valid(raise_exception=True)
        attrs.update(data.validated_data)
        return attrs


class MpesaCallbackSerializer(serializers.Serializer):
    Body = serializers.DictField()


class PesapalInitializationSerializer(serializers.Serializer):
    payer_email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=40)
    customer_name = serializers.CharField(required=False, allow_blank=True, max_length=160)

    def validate(self, attrs):
        data = PaymentInitializationSerializer(
            data={
                'method': 'pesapal',
                'phone_number': attrs.get('phone_number', ''),
                'payer_email': attrs.get('payer_email', ''),
            },
            context=self.context,
        )
        data.is_valid(raise_exception=True)
        attrs.update(data.validated_data)
        attrs['phone_number'] = (attrs.get('phone_number') or '').strip()
        attrs['customer_name'] = (attrs.get('customer_name') or '').strip()
        return attrs


class PesapalNotificationSerializer(serializers.Serializer):
    OrderTrackingId = serializers.CharField(required=False, allow_blank=True, max_length=128)
    OrderMerchantReference = serializers.CharField(required=False, allow_blank=True, max_length=128)
    OrderNotificationType = serializers.CharField(required=False, allow_blank=True, max_length=64)
    orderTrackingId = serializers.CharField(required=False, allow_blank=True, max_length=128)
    orderMerchantReference = serializers.CharField(required=False, allow_blank=True, max_length=128)
    orderNotificationType = serializers.CharField(required=False, allow_blank=True, max_length=64)
    order_tracking_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    order_merchant_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)
    order_notification_type = serializers.CharField(required=False, allow_blank=True, max_length=64)
    notification_type = serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate(self, attrs):
        request = self.context.get('request')
        query_params = getattr(request, 'query_params', None) or getattr(request, 'GET', {}) if request else {}
        order_tracking_id = (
            attrs.get('OrderTrackingId')
            or attrs.get('orderTrackingId')
            or attrs.get('order_tracking_id')
            or query_params.get('OrderTrackingId')
            or query_params.get('orderTrackingId')
            or query_params.get('order_tracking_id')
            or ''
        ).strip()
        merchant_reference = (
            attrs.get('OrderMerchantReference')
            or attrs.get('orderMerchantReference')
            or attrs.get('order_merchant_reference')
            or query_params.get('OrderMerchantReference')
            or query_params.get('orderMerchantReference')
            or query_params.get('order_merchant_reference')
            or ''
        ).strip()
        notification_type = (
            attrs.get('OrderNotificationType')
            or attrs.get('orderNotificationType')
            or attrs.get('order_notification_type')
            or attrs.get('notification_type')
            or query_params.get('OrderNotificationType')
            or query_params.get('orderNotificationType')
            or query_params.get('order_notification_type')
            or query_params.get('notification_type')
            or ''
        ).strip()
        if not order_tracking_id:
            raise serializers.ValidationError({'OrderTrackingId': 'Pesapal order tracking ID is required.'})
        attrs['order_tracking_id'] = order_tracking_id
        attrs['merchant_reference'] = merchant_reference
        attrs['notification_type'] = notification_type
        return attrs


class CardInitializationSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card')])
    payer_email = serializers.EmailField(required=False, allow_blank=True)
    payment_token = serializers.CharField(max_length=128)
    card_brand = serializers.CharField(required=False, allow_blank=True, max_length=32)
    last4 = serializers.CharField(required=False, allow_blank=True, max_length=4)
    expiry_month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    expiry_year = serializers.IntegerField(required=False, min_value=2024, max_value=2100)
    holder_name = serializers.CharField(required=False, allow_blank=True, max_length=120)

    def validate(self, attrs):
        data = PaymentInitializationSerializer(
            data={
                'method': attrs.get('method', ''),
                'payer_email': attrs.get('payer_email', ''),
            },
            context=self.context,
        )
        data.is_valid(raise_exception=True)
        attrs.update(data.validated_data)
        attrs['payment_token'] = (attrs.get('payment_token') or '').strip()
        attrs['card_brand'] = (attrs.get('card_brand') or '').strip()
        attrs['last4'] = (attrs.get('last4') or '').strip()
        attrs['holder_name'] = (attrs.get('holder_name') or '').strip()
        return attrs


class AirtelMoneyInitializationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=40)
    payer_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        data = PaymentInitializationSerializer(
            data={
                'method': 'airtel_money',
                'phone_number': attrs.get('phone_number', ''),
                'payer_email': attrs.get('payer_email', ''),
            },
            context=self.context,
        )
        data.is_valid(raise_exception=True)
        attrs.update(data.validated_data)
        return attrs


class AirtelMoneyCallbackSerializer(serializers.Serializer):
    reference = serializers.CharField(required=False, allow_blank=True, max_length=64)
    provider_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)
    status = serializers.CharField(required=False, allow_blank=True, max_length=64)
    transaction = serializers.DictField(required=False)
