from django.apps import apps
from phonenumber_field.phonenumber import PhoneNumber
from rest_framework import serializers


class BasketItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(required=False, min_value=1, default=1)

    def validate_product_id(self, value):
        Product = apps.get_model('catalogue', 'Product')
        try:
            product = Product.objects.get(id=value, is_public=True)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError('Unknown product.') from exc
        self.context['product'] = product
        return value

    def validate(self, attrs):
        request = self.context['request']
        product = self.context['product']
        quantity = attrs['quantity']
        stock_info = request.strategy.fetch_for_product(product)

        if not getattr(stock_info, 'stockrecord', None):
            raise serializers.ValidationError({'product_id': 'This product cannot be purchased yet.'})

        requested_total = request.basket.product_quantity(product) + quantity
        permitted, reason = stock_info.availability.is_purchase_permitted(requested_total)
        if not permitted:
            raise serializers.ValidationError({'quantity': str(reason)})

        attrs['product'] = product
        return attrs


class BasketLineUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)

    def validate_quantity(self, value):
        line = self.context['line']
        basket = self.context['request'].basket

        if value == 0:
            return value

        qty_delta = value - line.quantity
        permitted, reason = basket.is_quantity_allowed(qty_delta, line=line)
        if not permitted:
            raise serializers.ValidationError(str(reason))

        purchase_permitted, purchase_reason = line.purchase_info.availability.is_purchase_permitted(quantity=value)
        if not purchase_permitted:
            raise serializers.ValidationError(str(purchase_reason))
        return value


class ShippingAddressSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    line1 = serializers.CharField(max_length=255)
    line2 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    line3 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    line4 = serializers.CharField(max_length=255)
    state = serializers.CharField(required=False, allow_blank=True, max_length=255)
    postcode = serializers.CharField(required=False, allow_blank=True, max_length=64)
    country_code = serializers.CharField(max_length=2)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=128)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_country_code(self, value):
        Country = apps.get_model('address', 'Country')
        country = Country.objects.filter(
            iso_3166_1_a2__iexact=value,
            is_shipping_country=True,
        ).first()
        if not country:
            raise serializers.ValidationError('Unsupported shipping country.')
        self.context['country'] = country
        return country.iso_3166_1_a2

    def validate(self, attrs):
        country_code = (attrs.get('country_code') or '').strip().upper()
        if not (attrs.get('phone_number') or '').strip():
            raise serializers.ValidationError({'phone_number': 'Phone number is required for shipping updates.'})
        if country_code and country_code != 'KE' and not (attrs.get('postcode') or '').strip():
            raise serializers.ValidationError({'postcode': 'Postcode is required for international shipping.'})
        return attrs

    def to_session_fields(self) -> dict:
        data = self.validated_data
        country = self.context['country']
        phone_number = data.get('phone_number', '')
        if phone_number:
            phone_number = PhoneNumber.from_string(phone_number, region=country.iso_3166_1_a2)
        return {
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'line1': data['line1'],
            'line2': data.get('line2', ''),
            'line3': data.get('line3', ''),
            'line4': data['line4'],
            'state': data.get('state', ''),
            'postcode': data.get('postcode', ''),
            'country_id': country.pk,
            'phone_number': phone_number,
            'notes': data.get('notes', ''),
        }


class ShippingMethodSelectionSerializer(serializers.Serializer):
    method_code = serializers.CharField(max_length=128)
