from django.apps import apps
from django.db import transaction
from django.template.defaultfilters import slugify
from rest_framework import serializers


class ProductListQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(required=False, allow_blank=True)
    in_stock = serializers.BooleanField(required=False)
    min_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    max_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    sort_by = serializers.ChoiceField(
        required=False,
        default="relevance",
        choices=[
            "relevance",
            "newest",
            "price_asc",
            "price_desc",
            "title_asc",
        ],
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=60, default=24)


class QuoteRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, min_value=1)
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    message = serializers.CharField(max_length=1500)


class ProductWriteSerializer(serializers.Serializer):
    upc = serializers.CharField(required=False, max_length=128)
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_public = serializers.BooleanField(required=False)
    category_ids = serializers.ListField(
        required=False,
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )
    product_class = serializers.CharField(required=False, allow_blank=False, max_length=128)
    partner_id = serializers.IntegerField(required=False, min_value=1)
    partner_name = serializers.CharField(required=False, allow_blank=False, max_length=128)
    partner_sku = serializers.CharField(required=False, allow_blank=True, max_length=128)
    price = serializers.DecimalField(required=False, allow_null=True, max_digits=12, decimal_places=2, min_value=0)
    currency = serializers.CharField(required=False, allow_blank=False, max_length=12)
    num_in_stock = serializers.IntegerField(required=False, min_value=0)
    attributes = serializers.DictField(
        required=False,
        child=serializers.CharField(required=False, allow_blank=True, allow_null=True),
    )

    DEFAULT_PRODUCT_CLASS = 'Industrial Product'
    DEFAULT_PARTNER_NAME = 'Default Partner'
    DEFAULT_CURRENCY = 'USD'

    def validate(self, attrs):
        Product = apps.get_model('catalogue', 'Product')
        Category = apps.get_model('catalogue', 'Category')
        is_create = self.instance is None
        requires_full_payload = is_create or not self.partial
        required_errors = {}

        if requires_full_payload and not attrs.get('upc'):
            required_errors['upc'] = 'This field is required.'
        if requires_full_payload and not attrs.get('title'):
            required_errors['title'] = 'This field is required.'
        if required_errors:
            raise serializers.ValidationError(required_errors)

        upc = attrs.get('upc')
        if upc:
            queryset = Product.objects.filter(upc=upc)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'upc': 'A product with this UPC already exists.'})

        if 'category_ids' in attrs:
            categories = list(Category.objects.filter(id__in=attrs['category_ids']).order_by('id'))
            found_ids = {category.id for category in categories}
            missing_ids = [category_id for category_id in attrs['category_ids'] if category_id not in found_ids]
            if missing_ids:
                raise serializers.ValidationError(
                    {'category_ids': f"Unknown category ids: {', '.join(str(category_id) for category_id in missing_ids)}"}
                )
            attrs['resolved_categories'] = categories

        if 'product_class' in attrs or is_create:
            attrs['resolved_product_class_name'] = attrs.get('product_class') or self.DEFAULT_PRODUCT_CLASS

        stock_requested = is_create or any(
            field in attrs for field in ('price', 'currency', 'num_in_stock', 'partner_sku', 'partner_id', 'partner_name')
        )
        attrs['stock_requested'] = stock_requested
        if attrs.get('partner_id'):
            self._get_partner_by_id(attrs['partner_id'])

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        Product = apps.get_model('catalogue', 'Product')

        categories = validated_data.pop('resolved_categories', None)
        product_class_name = validated_data.pop('resolved_product_class_name', self.DEFAULT_PRODUCT_CLASS)
        product_class = self._get_or_create_product_class(product_class_name)
        attributes = validated_data.pop('attributes', {})
        stock_requested = validated_data.pop('stock_requested', False)

        validated_data.pop('product_class', None)

        product = Product.objects.create(
            upc=validated_data['upc'],
            title=validated_data['title'],
            description=validated_data.get('description') or '',
            is_public=validated_data.get('is_public', True),
            product_class=product_class,
            structure=getattr(Product, 'STANDALONE', 'standalone'),
        )

        if categories is not None:
            product.categories.set(categories)

        if stock_requested:
            partner = self._resolve_partner(product=product, payload=validated_data)
            self._save_stockrecord(product=product, partner=partner, payload=validated_data)

        self._save_attributes(product=product, product_class=product_class, attributes=attributes)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        categories = validated_data.pop('resolved_categories', None)
        product_class_name = validated_data.pop('resolved_product_class_name', None)
        attributes = validated_data.pop('attributes', None)
        stock_requested = validated_data.pop('stock_requested', False)

        validated_data.pop('product_class', None)

        product_class = self._get_or_create_product_class(product_class_name) if product_class_name else instance.product_class
        dirty_fields = []

        for field in ('upc', 'title', 'is_public'):
            if field in validated_data and getattr(instance, field) != validated_data[field]:
                setattr(instance, field, validated_data[field])
                dirty_fields.append(field)

        if 'description' in validated_data:
            description = validated_data.get('description') or ''
            if (instance.description or '') != description:
                instance.description = description
                dirty_fields.append('description')

        if instance.product_class_id != getattr(product_class, 'id', None):
            instance.product_class = product_class
            dirty_fields.append('product_class')

        expected_structure = getattr(instance.__class__, 'STANDALONE', 'standalone')
        if instance.structure != expected_structure:
            instance.structure = expected_structure
            dirty_fields.append('structure')

        if dirty_fields:
            instance.save(update_fields=dirty_fields)

        if categories is not None:
            instance.categories.set(categories)

        if stock_requested:
            partner = self._resolve_partner(product=instance, payload=validated_data)
            self._save_stockrecord(product=instance, partner=partner, payload=validated_data)

        if attributes is not None:
            self._save_attributes(product=instance, product_class=product_class, attributes=attributes)

        return instance

    def _get_or_create_product_class(self, name: str):
        ProductClass = apps.get_model('catalogue', 'ProductClass')
        product_class, _ = ProductClass.objects.get_or_create(name=name)
        return product_class

    def _get_partner_by_id(self, partner_id: int):
        Partner = apps.get_model('partner', 'Partner')
        try:
            return Partner.objects.get(id=partner_id)
        except Partner.DoesNotExist as exc:
            raise serializers.ValidationError({'partner_id': 'Unknown partner.'}) from exc

    def _resolve_partner(self, product, payload):
        Partner = apps.get_model('partner', 'Partner')

        partner_id = payload.get('partner_id')
        if partner_id:
            return self._get_partner_by_id(partner_id)

        partner_name = payload.get('partner_name')
        if not partner_name:
            existing_stockrecord = product.stockrecords.select_related('partner').order_by('id').first()
            if existing_stockrecord:
                return existing_stockrecord.partner
            partner_name = self.DEFAULT_PARTNER_NAME

        code = slugify(partner_name).replace('-', '_')[:128] or 'default_partner'
        partner, _ = Partner.objects.get_or_create(code=code, defaults={'name': partner_name})
        if partner.name != partner_name:
            partner.name = partner_name
            partner.save(update_fields=['name'])
        return partner

    def _save_stockrecord(self, product, partner, payload):
        StockRecord = apps.get_model('partner', 'StockRecord')

        stockrecord = None
        existing_records = product.stockrecords.select_related('partner').order_by('id')

        if partner is not None:
            stockrecord = existing_records.filter(partner=partner).first()

        if stockrecord is None:
            stockrecord = existing_records.first()
            if stockrecord is not None and partner is not None:
                stockrecord.partner = partner

        if stockrecord is None:
            stockrecord = StockRecord(product=product, partner=partner)

        is_create = stockrecord.pk is None

        if 'partner_sku' in payload or is_create:
            stockrecord.partner_sku = payload.get('partner_sku') or product.upc
        if 'currency' in payload or is_create:
            stockrecord.price_currency = payload.get('currency') or self.DEFAULT_CURRENCY
        if 'price' in payload or is_create:
            stockrecord.price = payload.get('price')
        if 'num_in_stock' in payload or is_create:
            stockrecord.num_in_stock = payload.get('num_in_stock', 0)

        stockrecord.save()
        return stockrecord

    def _save_attributes(self, product, product_class, attributes):
        ProductAttribute = apps.get_model('catalogue', 'ProductAttribute')

        for raw_code, raw_value in (attributes or {}).items():
            code = self._normalize_attribute_code(raw_code)
            if not code:
                continue

            attribute, _ = ProductAttribute.objects.get_or_create(
                product_class=product_class,
                code=code,
                defaults={
                    'name': code.replace('_', ' ').title(),
                    'type': ProductAttribute.TEXT,
                    'required': False,
                },
            )

            value = '' if raw_value is None else str(raw_value).strip()
            if not value:
                product.attribute_values.filter(attribute=attribute).delete()
                continue

            attribute.save_value(product, value)

    @staticmethod
    def _normalize_attribute_code(raw_code) -> str:
        normalized = slugify(str(raw_code or '')).replace('-', '_')
        return normalized[:128]
