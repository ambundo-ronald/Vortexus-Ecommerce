from django.apps import apps
from django.db import transaction
from django.template.defaultfilters import slugify
from rest_framework import serializers

from apps.common.currency import default_currency
from apps.common.media import normalize_uploaded_image
from apps.recommendations.services import RecommendationService


class ProductListQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, choices=["active", "draft"], allow_blank=True)
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


class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    alt = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_image(self, value):
        try:
            return normalize_uploaded_image(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class ProductWriteSerializer(serializers.Serializer):
    upc = serializers.CharField(required=False, max_length=128)
    title = serializers.CharField(required=False, max_length=255)
    slug = serializers.SlugField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
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
    recommended_product_ids = serializers.ListField(
        required=False,
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    DEFAULT_PRODUCT_CLASS = 'Industrial Product'
    DEFAULT_PARTNER_NAME = 'Default Partner'
    DEFAULT_CURRENCY = default_currency()

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

        if 'recommended_product_ids' in attrs:
            recommended_ids = list(dict.fromkeys(attrs['recommended_product_ids']))
            if self.instance is not None:
                recommended_ids = [product_id for product_id in recommended_ids if product_id != self.instance.pk]
            products = list(Product.objects.filter(id__in=recommended_ids).order_by('id'))
            found_ids = {product.id for product in products}
            missing_ids = [product_id for product_id in recommended_ids if product_id not in found_ids]
            if missing_ids:
                raise serializers.ValidationError(
                    {'recommended_product_ids': f"Unknown product ids: {', '.join(str(product_id) for product_id in missing_ids)}"}
                )
            attrs['resolved_recommended_products'] = products

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
        recommended_products = validated_data.pop('resolved_recommended_products', None)
        stock_requested = validated_data.pop('stock_requested', False)

        validated_data.pop('product_class', None)
        validated_data.pop('recommended_product_ids', None)

        product = Product.objects.create(
            upc=validated_data['upc'],
            title=validated_data['title'],
            slug=validated_data.get('slug') or slugify(validated_data['title']),
            description=validated_data.get('description') or '',
            meta_title=validated_data.get('meta_title') or '',
            meta_description=validated_data.get('meta_description') or '',
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
        if recommended_products is not None:
            self._save_recommendations(product=product, recommended_products=recommended_products)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        categories = validated_data.pop('resolved_categories', None)
        product_class_name = validated_data.pop('resolved_product_class_name', None)
        attributes = validated_data.pop('attributes', None)
        recommended_products = validated_data.pop('resolved_recommended_products', None)
        stock_requested = validated_data.pop('stock_requested', False)

        validated_data.pop('product_class', None)
        validated_data.pop('recommended_product_ids', None)

        product_class = self._get_or_create_product_class(product_class_name) if product_class_name else instance.product_class
        dirty_fields = []

        for field in ('upc', 'title', 'slug', 'meta_title', 'meta_description', 'is_public'):
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

        if recommended_products is not None:
            self._save_recommendations(product=instance, recommended_products=recommended_products)

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
        previous_price = getattr(stockrecord, 'price', None)
        previous_currency = getattr(stockrecord, 'price_currency', None) or self.DEFAULT_CURRENCY

        if 'partner_sku' in payload or is_create:
            stockrecord.partner_sku = payload.get('partner_sku') or product.upc
        if 'currency' in payload or is_create:
            stockrecord.price_currency = payload.get('currency') or self.DEFAULT_CURRENCY
        if 'price' in payload or is_create:
            stockrecord.price = payload.get('price')
        if 'num_in_stock' in payload or is_create:
            stockrecord.num_in_stock = payload.get('num_in_stock', 0)

        stockrecord.save()
        self._save_price_snapshot(
            stockrecord=stockrecord,
            previous_price=previous_price,
            previous_currency=previous_currency,
            is_create=is_create,
        )
        return stockrecord

    def _save_price_snapshot(self, stockrecord, previous_price, previous_currency, is_create: bool) -> None:
        PriceSnapshot = apps.get_model('inventory', 'StockRecordPriceSnapshot')
        current_price = getattr(stockrecord, 'price', None)
        current_currency = getattr(stockrecord, 'price_currency', None) or self.DEFAULT_CURRENCY

        if current_price is None:
            return

        if is_create or previous_price is None:
            PriceSnapshot.objects.update_or_create(
                stockrecord=stockrecord,
                defaults={
                    'current_price': current_price,
                    'current_currency': current_currency,
                },
            )
            return

        if previous_price == current_price and (previous_currency or '') == (current_currency or ''):
            PriceSnapshot.objects.update_or_create(
                stockrecord=stockrecord,
                defaults={
                    'current_price': current_price,
                    'current_currency': current_currency,
                },
            )
            return

        PriceSnapshot.objects.update_or_create(
            stockrecord=stockrecord,
            defaults={
                'previous_price': previous_price,
                'previous_currency': previous_currency or current_currency,
                'current_price': current_price,
                'current_currency': current_currency,
            },
        )

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

    def _save_recommendations(self, product, recommended_products):
        ProductRecommendation = apps.get_model('catalogue', 'ProductRecommendation')

        ProductRecommendation.objects.filter(primary=product).delete()
        rows = [
            ProductRecommendation(primary=product, recommendation=recommended_product, ranking=index)
            for index, recommended_product in enumerate(recommended_products, start=1)
            if recommended_product.pk != product.pk
        ]
        if rows:
            ProductRecommendation.objects.bulk_create(rows)
        RecommendationService.clear_product_cache(product.id)

    @staticmethod
    def _normalize_attribute_code(raw_code) -> str:
        normalized = slugify(str(raw_code or '')).replace('-', '_')
        return normalized[:128]
