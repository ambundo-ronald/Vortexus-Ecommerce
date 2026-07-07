import logging

from django.apps import apps
from django.db import transaction
from django.template.defaultfilters import slugify
from rest_framework import serializers

from .product_domain_router import ProductDomainRouter

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, serializer, router: ProductDomainRouter | None = None):
        self.serializer = serializer
        self.router = router or ProductDomainRouter()

    @transaction.atomic
    def create(self, validated_data):
        Product = apps.get_model('catalogue', 'Product')

        categories = validated_data.pop('resolved_categories', None)
        product_class_name = validated_data.pop('resolved_product_class_name', self.serializer.DEFAULT_PRODUCT_CLASS)
        product_class = self.serializer._get_or_create_product_class(product_class_name)
        attributes = validated_data.pop('attributes', {})
        domain_specs = validated_data.pop('domain_specs', None)
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

        stockrecord = None
        if stock_requested:
            partner = self.serializer._resolve_partner(product=product, payload=validated_data)
            stockrecord = self.serializer._save_stockrecord(product=product, partner=partner, payload=validated_data)

        self.serializer._save_attributes(product=product, product_class=product_class, attributes=attributes)
        if recommended_products is not None:
            self.serializer._save_recommendations(product=product, recommended_products=recommended_products)

        if domain_specs is not None:
            self._sync_domain_product(
                product=product,
                product_class_name=product_class_name,
                domain_specs=domain_specs,
                stockrecord=stockrecord,
            )

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        categories = validated_data.pop('resolved_categories', None)
        product_class_name = validated_data.pop('resolved_product_class_name', None)
        attributes = validated_data.pop('attributes', None)
        domain_specs = validated_data.pop('domain_specs', None)
        recommended_products = validated_data.pop('resolved_recommended_products', None)
        stock_requested = validated_data.pop('stock_requested', False)

        validated_data.pop('product_class', None)
        validated_data.pop('recommended_product_ids', None)

        product_class = self.serializer._get_or_create_product_class(product_class_name) if product_class_name else instance.product_class
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

        stockrecord = None
        if stock_requested:
            partner = self.serializer._resolve_partner(product=instance, payload=validated_data)
            stockrecord = self.serializer._save_stockrecord(product=instance, partner=partner, payload=validated_data)
        else:
            stockrecord = instance.stockrecords.order_by('id').first()

        if attributes is not None:
            self.serializer._save_attributes(product=instance, product_class=product_class, attributes=attributes)

        if recommended_products is not None:
            self.serializer._save_recommendations(product=instance, recommended_products=recommended_products)

        if domain_specs is not None:
            self._sync_domain_product(
                product=instance,
                product_class_name=product_class_name or getattr(product_class, 'name', ''),
                domain_specs=domain_specs,
                stockrecord=stockrecord,
            )

        return instance

    def _sync_domain_product(self, *, product, product_class_name: str, domain_specs: dict, stockrecord=None):
        ProductMongoReference = apps.get_model('accounts', 'ProductMongoReference')
        reference = getattr(product, 'mongo_reference', None)

        created_mongo_document = False
        if reference and reference.mongo_id:
            result = self.router.update(
                mongo_id=reference.mongo_id,
                product=product,
                product_class=product_class_name,
                specs=domain_specs,
                stockrecord=stockrecord,
            )
        else:
            result = self.router.create(
                product=product,
                product_class=product_class_name,
                specs=domain_specs,
                stockrecord=stockrecord,
            )
            created_mongo_document = True

        try:
            ProductMongoReference.objects.update_or_create(
                product=product,
                defaults={
                    'product_class': ProductDomainRouter.normalize_product_class(product_class_name),
                    'mongo_id': result['mongo_id'],
                    'collection': result.get('collection', ''),
                    'payload': result.get('payload') or {},
                },
            )
        except Exception:
            if created_mongo_document:
                try:
                    self.router.delete(result['mongo_id'])
                except serializers.ValidationError:
                    logger.warning('Failed to delete orphan Mongo product %s after Django rollback', result['mongo_id'])
            raise
        logger.info('Synced product %s to Mongo collection %s', product.id, result.get('collection', ''))

    def merge_domain_payload(self, product, detail: dict) -> dict:
        reference = getattr(product, 'mongo_reference', None)
        if not reference:
            return detail

        domain = {
            'mongo_id': reference.mongo_id,
            'product_class': reference.product_class,
            'collection': reference.collection,
            'last_synced_at': reference.last_synced_at,
            'payload': reference.payload or {},
        }

        try:
            domain['payload'] = self.router.get(reference.mongo_id).get('data', {}).get('product') or domain['payload']
        except serializers.ValidationError:
            logger.info('Using cached Mongo payload for product %s', product.id)

        return {**detail, 'domain_product': domain}
