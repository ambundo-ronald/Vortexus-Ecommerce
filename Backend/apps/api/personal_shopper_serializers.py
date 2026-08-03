from django.apps import apps
from django.utils import timezone
from rest_framework import serializers

from apps.common.products import serialize_product_card
from apps.personal_shopper.models import ShopperList, ShopperListItem


class ShopperListItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=999, default=1)
    note = serializers.CharField(max_length=300, required=False, allow_blank=True, default='')


class ShopperListWriteSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=160)
    note = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.ChoiceField(choices=ShopperList.Status.choices, required=False, default=ShopperList.Status.DRAFT)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    items = ShopperListItemWriteSerializer(many=True, allow_empty=False)

    def validate_customer_id(self, value):
        User = apps.get_model('auth', 'User')
        customer = User.objects.filter(id=value, is_active=True, is_staff=False).first()
        if not customer:
            raise serializers.ValidationError('Select an active registered customer.')
        return value

    def validate_items(self, value):
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('A product can only appear once in a list.')
        Product = apps.get_model('catalogue', 'Product')
        found = set(Product.objects.filter(id__in=product_ids, is_public=True).values_list('id', flat=True))
        missing = set(product_ids) - found
        if missing:
            raise serializers.ValidationError(f'Unknown or unavailable products: {sorted(missing)}')
        return value

    def validate(self, attrs):
        expires_at = attrs.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError({'expires_at': 'Expiry must be in the future.'})
        if attrs.get('status') in {ShopperList.Status.VIEWED, ShopperList.Status.ADDED_TO_CART}:
            raise serializers.ValidationError({'status': 'Staff cannot set this status directly.'})
        return attrs


def shopper_list_payload(
    shopper_list,
    display_currency=None,
    include_token=False,
    include_tax=False,
    tax_country_code=None,
):
    customer = shopper_list.customer
    payload = {
        'id': shopper_list.id,
        'title': shopper_list.title,
        'note': shopper_list.note,
        'status': shopper_list.status,
        'expires_at': shopper_list.expires_at,
        'viewed_at': shopper_list.viewed_at,
        'added_to_cart_at': shopper_list.added_to_cart_at,
        'date_created': shopper_list.date_created,
        'date_updated': shopper_list.date_updated,
        'customer': {
            'id': customer.id,
            'email': customer.email,
            'name': customer.get_full_name() or customer.email,
        },
        'created_by': {
            'id': shopper_list.created_by_id,
            'name': shopper_list.created_by.get_full_name() or shopper_list.created_by.email,
        },
        'items': [
            {
                'id': item.id,
                'quantity': item.quantity,
                'note': item.note,
                'product': serialize_product_card(
                    item.product,
                    display_currency=display_currency,
                    include_tax=include_tax,
                    tax_country_code=tax_country_code,
                ),
            }
            for item in shopper_list.items.all()
        ],
    }
    if include_token:
        payload['share_token'] = str(shopper_list.share_token)
    return payload


def replace_shopper_list_items(shopper_list, items):
    Product = apps.get_model('catalogue', 'Product')
    products = Product.objects.in_bulk([item['product_id'] for item in items])
    shopper_list.items.all().delete()
    ShopperListItem.objects.bulk_create([
        ShopperListItem(
            shopper_list=shopper_list,
            product=products[item['product_id']],
            quantity=item['quantity'],
            note=item.get('note', ''),
            position=position,
        )
        for position, item in enumerate(items)
    ])
