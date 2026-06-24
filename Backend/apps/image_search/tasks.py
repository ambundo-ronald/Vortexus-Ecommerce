import logging
from typing import Any

from celery import shared_task
from django.core.files.storage import default_storage
from django.apps import apps
from django.conf import settings
from opensearchpy import NotFoundError
from opensearchpy.exceptions import OpenSearchException

from apps.common.clients import get_opensearch_client
from apps.common.catalog import brand_slug, product_brand
from apps.common.products import (
    stockrecord_count,
    stockrecord_currency,
    stockrecord_previous_currency,
    stockrecord_previous_price,
    stockrecord_price,
)

from .services import ImageEmbeddingService

logger = logging.getLogger(__name__)


def _product_image_file(product):
    try:
        image = product.primary_image()
    except Exception:
        return None

    if not image or not getattr(image, 'original', None):
        return None

    file_field = image.original
    if not file_field.name:
        return None

    return file_field


def _safe_file_url(file_field) -> str:
    if not file_field:
        return ''
    try:
        return file_field.url
    except Exception:
        return ''


def _category_slug(product) -> str:
    slugs = _category_slugs(product)
    return slugs[-1] if slugs else ''


def _category_slugs(product) -> list[str]:
    slugs: list[str] = []
    for category in product.categories.all():
        try:
            ancestors = list(category.get_ancestors()) + [category]
        except Exception:
            ancestors = [category]
        slugs.extend(item.slug for item in ancestors if getattr(item, 'slug', ''))
    return list(dict.fromkeys(slugs))


def _index_document(product, embedding: list[float], file_field) -> dict[str, Any]:
    stockrecord = product.stockrecords.first()
    brand = product_brand(product)

    return {
        'product_id': product.id,
        'title': product.title,
        'sku': product.upc,
        'category_slug': _category_slug(product),
        'category_slugs': _category_slugs(product),
        'brand': brand,
        'brand_slug': brand_slug(brand),
        'price': stockrecord_price(stockrecord),
        'currency': stockrecord_currency(stockrecord),
        'previous_price': stockrecord_previous_price(stockrecord),
        'previous_currency': stockrecord_previous_currency(stockrecord),
        'thumbnail': _safe_file_url(file_field),
        'in_stock': stockrecord_count(stockrecord) > 0,
        'stock_count': stockrecord_count(stockrecord),
        'num_in_stock': stockrecord_count(stockrecord),
        'embedding': embedding,
    }


def _delete_embedding_doc(client, product_id: int) -> None:
    try:
        client.delete(index=settings.SEARCH_INDEX_IMAGE_EMBEDDINGS, id=product_id, refresh=False)
    except NotFoundError:
        return


def _existing_embedding(client, product_id: int) -> list[float] | None:
    try:
        response = client.get(index=settings.SEARCH_INDEX_IMAGE_EMBEDDINGS, id=product_id)
    except NotFoundError:
        return None
    source = response.get('_source', {})
    embedding = source.get('embedding')
    if isinstance(embedding, list) and embedding:
        return embedding
    return None


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def sync_product_image_index(self, product_id: int, regenerate_embedding: bool = False) -> dict[str, Any]:
    Product = apps.get_model('catalogue', 'Product')
    product = (
        Product.objects.filter(id=product_id, is_public=True)
        .prefetch_related('categories', 'stockrecords', 'attribute_values__attribute')
        .first()
    )

    client = get_opensearch_client()

    if not product:
        _delete_embedding_doc(client=client, product_id=product_id)
        return {'product_id': product_id, 'status': 'skipped', 'reason': 'product-not-found'}

    file_field = _product_image_file(product)
    if not file_field:
        _delete_embedding_doc(client=client, product_id=product_id)
        return {'product_id': product_id, 'status': 'skipped', 'reason': 'missing-image'}
    if not default_storage.exists(file_field.name):
        logger.warning(
            'Skipping image embedding for product %s because image file is missing: %s',
            product_id,
            file_field.name,
        )
        _delete_embedding_doc(client=client, product_id=product_id)
        return {'product_id': product_id, 'status': 'skipped', 'reason': 'missing-image-file'}

    embedding = None if regenerate_embedding else _existing_embedding(client, product_id)
    if embedding is None:
        file_field.open('rb')
        try:
            embedding = ImageEmbeddingService().embed_image(file_field)
        finally:
            file_field.close()

    document = _index_document(product=product, embedding=embedding, file_field=file_field)
    client.index(
        index=settings.SEARCH_INDEX_IMAGE_EMBEDDINGS,
        id=product.id,
        body=document,
        refresh=False,
    )

    return {
        'product_id': product.id,
        'status': 'indexed',
        'dimension': len(embedding),
        'regenerated_embedding': regenerate_embedding or embedding is not None,
    }


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def generate_product_image_embedding(self, product_id: int) -> dict[str, Any]:
    return sync_product_image_index.run(product_id=product_id, regenerate_embedding=True)


@shared_task
def remove_product_image_embedding(product_id: int) -> bool:
    client = get_opensearch_client()
    _delete_embedding_doc(client=client, product_id=product_id)
    return True


@shared_task(bind=True)
def backfill_product_image_embeddings(self, limit: int | None = None) -> int:
    Product = apps.get_model('catalogue', 'Product')
    queryset = Product.objects.filter(is_public=True).order_by('id').values_list('id', flat=True)
    if limit:
        queryset = queryset[:limit]

    indexed = 0
    for product_id in queryset:
        result = sync_product_image_index.run(product_id=product_id, regenerate_embedding=True)
        if result.get('status') == 'indexed':
            indexed += 1

    return indexed
