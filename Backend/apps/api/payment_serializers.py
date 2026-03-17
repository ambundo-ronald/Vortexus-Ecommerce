from rest_framework import serializers

from apps.payments.services import available_payment_methods, get_payment_method

from .checkout_utils import get_selected_shipping_method, get_shipping_address
from .order_serializers import build_order_prices


class PaymentMethodSerializer(serializers.Serializer):
    def to_representation(self, method):
        return method


class PaymentInitializationSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[(method['code'], method['name']) for method in available_payment_methods()])
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
        if basket.is_shipping_required() and not shipping_address:
            raise serializers.ValidationError({'shipping_address': 'Shipping address is required before payment initialization.'})
        if basket.is_shipping_required() and not shipping_method:
            raise serializers.ValidationError({'shipping_method': 'Shipping method is required before payment initialization.'})

        if method.get('requires_phone') and not (attrs.get('phone_number') or '').strip():
            raise serializers.ValidationError({'phone_number': f"{method['name']} requires a phone number."})

        attrs['shipping_address'] = shipping_address
        attrs['shipping_method'] = shipping_method
        attrs['pricing'] = build_order_prices(basket, shipping_address, shipping_method)
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
