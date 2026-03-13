from django.apps import apps
from django.db.models import Count
from rest_framework import serializers

from apps.common.products import serialize_product_card


def get_wishlist_model():
    return apps.get_model('wishlists', 'WishList')


def get_wishlist_line_model():
    return apps.get_model('wishlists', 'Line')


def default_wishlist_name() -> str:
    return 'Saved Items'


def get_default_wishlist(user, create: bool = False):
    WishList = get_wishlist_model()
    wishlist = (
        WishList.objects.filter(owner=user, name=default_wishlist_name())
        .order_by('date_created', 'id')
        .first()
    )
    if wishlist or not create:
        return wishlist
    return WishList.objects.create(owner=user, name=default_wishlist_name())


def wishlist_summary_payload(wishlist, default_wishlist_id: int | None = None):
    line_count = getattr(wishlist, 'line_count', None)
    if line_count is None:
        line_count = wishlist.lines.count()
    return {
        'id': wishlist.id,
        'name': wishlist.name,
        'key': wishlist.key,
        'visibility': wishlist.visibility,
        'line_count': line_count,
        'is_default': wishlist.id == default_wishlist_id,
        'date_created': wishlist.date_created,
    }


def wishlist_line_payload(line):
    product = line.product
    return {
        'id': line.id,
        'quantity': line.quantity,
        'title': line.get_title(),
        'product_id': product.id if product else None,
        'product': serialize_product_card(product) if product else None,
    }


def wishlist_detail_payload(wishlist, default_wishlist_id: int | None = None):
    return {
        **wishlist_summary_payload(wishlist, default_wishlist_id=default_wishlist_id),
        'items': [wishlist_line_payload(line) for line in wishlist.lines.all()],
    }


class WishListCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    visibility = serializers.ChoiceField(
        required=False,
        choices=['Private', 'Shared', 'Public'],
        default='Private',
    )

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Wishlist name cannot be blank.')
        return cleaned

    def create(self, validated_data):
        WishList = get_wishlist_model()
        return WishList.objects.create(
            owner=self.context['request'].user,
            name=validated_data['name'],
            visibility=validated_data.get('visibility', 'Private'),
        )


class WishListUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    visibility = serializers.ChoiceField(required=False, choices=['Private', 'Shared', 'Public'])

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Wishlist name cannot be blank.')
        return cleaned

    def update(self, instance, validated_data):
        dirty_fields = []
        for field in ('name', 'visibility'):
            if field in validated_data and getattr(instance, field) != validated_data[field]:
                setattr(instance, field, validated_data[field])
                dirty_fields.append(field)
        if dirty_fields:
            instance.save(update_fields=dirty_fields)
        return instance


class WishListAddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(required=False, min_value=1, default=1)

    def validate_product_id(self, value):
        Product = apps.get_model('catalogue', 'Product')
        product = (
            Product.objects.filter(is_public=True)
            .exclude(structure='parent')
            .prefetch_related('stockrecords', 'images', 'categories')
            .filter(id=value)
            .first()
        )
        if product is None:
            raise serializers.ValidationError('Unknown product.')
        self.context['product'] = product
        return value

    def save(self, **kwargs):
        wishlist = self.context['wishlist']
        product = self.context['product']
        quantity = self.validated_data.get('quantity', 1)

        line_model = get_wishlist_line_model()
        line, created = line_model.objects.get_or_create(
            wishlist=wishlist,
            product=product,
            defaults={
                'quantity': quantity,
                'title': product.get_title(),
            },
        )

        if not created:
            line.quantity += quantity
            line.title = product.get_title()
            line.save(update_fields=['quantity', 'title'])

        return line


class WishListBulkStatusQuerySerializer(serializers.Serializer):
    product_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


def user_wishlist_queryset(user):
    WishList = get_wishlist_model()
    return (
        WishList.objects.filter(owner=user)
        .annotate(line_count=Count('lines'))
        .prefetch_related('lines__product__stockrecords', 'lines__product__images')
        .order_by('-date_created', '-id')
    )
