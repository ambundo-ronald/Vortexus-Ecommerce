import logging
from typing import Any

from celery import shared_task
from django.apps import apps
from django.conf import settings
from opensearchpy import NotFoundError
from opensearchpy.exceptions import OpenSearchException

from apps.common.clients import get_opensearch_client

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
    category = product.categories.first()
    if category:
        return category.slug
    return ''


def _index_document(product, embedding: list[float], file_field) -> dict[str, Any]:
    stockrecord = product.stockrecords.first()

    return {
        'product_id': product.id,
        'title': product.title,
        'sku': product.upc,
        'category_slug': _category_slug(product),
        'price': float(stockrecord.price_excl_tax) if stockrecord and stockrecord.price_excl_tax is not None else None,
        'currency': stockrecord.price_currency if stockrecord and stockrecord.price_currency else 'USD',
        'thumbnail': _safe_file_url(file_field),
        'in_stock': bool(stockrecord and (stockrecord.num_in_stock or 0) > 0),
        'embedding': embedding,
    }


def _delete_embedding_doc(client, product_id: int) -> None:
    try:
        client.delete(index=settings.SEARCH_INDEX_IMAGE_EMBEDDINGS, id=product_id, refresh=False)
    except NotFoundError:
        return


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def generate_product_image_embedding(self, product_id: int) -> dict[str, Any]:
    Product = apps.get_model('catalogue', 'Product')
    product = (
        Product.objects.filter(id=product_id, is_public=True)
        .prefetch_related('categories', 'stockrecords')
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
    }


@shared_task(bind=True)
def backfill_product_image_embeddings(self, limit: int | None = None) -> int:
    Product = apps.get_model('catalogue', 'Product')
    queryset = Product.objects.filter(is_public=True).order_by('id').values_list('id', flat=True)
    if limit:
        queryset = queryset[:limit]

    indexed = 0
    for product_id in queryset:
        result = generate_product_image_embedding.run(product_id=product_id)
        if result.get('status') == 'indexed':
            indexed += 1

    return indexed
