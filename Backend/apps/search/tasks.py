from typing import Any

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.db.models import Avg, Count
from opensearchpy import NotFoundError
from opensearchpy.exceptions import OpenSearchException
from opensearchpy.helpers import bulk

from apps.common.clients import get_opensearch_client
from apps.common.products import stockrecord_currency, stockrecord_price


def _build_product_document(product: Any) -> dict[str, Any]:
    stockrecord = product.stockrecords.first()
    Review = apps.get_model('reviews', 'ProductReview')
    review_stats = Review.objects.filter(product=product, status=Review.APPROVED).aggregate(
        rating=Avg('score'),
        review_count=Count('id'),
    )

    image_url = ''
    try:
        image = product.primary_image()
        if image and getattr(image, 'original', None):
            image_url = image.original.url or ''
    except Exception:
        image_url = ''

    attributes_text = ''
    if hasattr(product, 'attribute_values'):
        attributes_text = ' '.join(
            value.value_as_text for value in product.attribute_values.all() if value.value_as_text
        )

    category_slug = ''
    first_category = product.categories.first()
    if first_category:
        category_slug = first_category.slug

    return {
        'id': product.id,
        'title': product.title,
        'sku': product.upc,
        'description': product.description,
        'category_slug': category_slug,
        'price': stockrecord_price(stockrecord),
        'currency': stockrecord_currency(stockrecord),
        'thumbnail': image_url,
        'in_stock': bool(stockrecord and (stockrecord.num_in_stock or 0) > 0),
        'rating': float(review_stats['rating']) if review_stats['rating'] is not None else None,
        'review_count': review_stats['review_count'] or 0,
        'date_updated': product.date_updated.isoformat() if getattr(product, 'date_updated', None) else None,
        'attributes_text': attributes_text,
    }


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def index_product_for_search(self, product_id: int) -> bool:
    Product = apps.get_model('catalogue', 'Product')
    product = (
        Product.objects.filter(id=product_id, is_public=True)
        .prefetch_related('categories', 'stockrecords', 'attribute_values')
        .first()
    )
    if not product:
        delete_product_from_search.run(product_id=product_id)
        return False

    client = get_opensearch_client()
    document = _build_product_document(product)
    client.index(index=settings.SEARCH_INDEX_PRODUCTS, id=product.id, body=document, refresh=False)
    return True


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def delete_product_from_search(self, product_id: int) -> bool:
    client = get_opensearch_client()
    try:
        client.delete(index=settings.SEARCH_INDEX_PRODUCTS, id=product_id, refresh=False)
    except NotFoundError:
        return False
    return True


@shared_task(bind=True, autoretry_for=(OpenSearchException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def reindex_all_products(self, batch_size: int = 500) -> int:
    Product = apps.get_model('catalogue', 'Product')
    count = 0
    client = get_opensearch_client()
    product_ids = list(Product.objects.filter(is_public=True).values_list('id', flat=True))

    for start in range(0, len(product_ids), batch_size):
        batch_ids = product_ids[start : start + batch_size]
        products = (
            Product.objects.filter(id__in=batch_ids, is_public=True)
            .prefetch_related('categories', 'stockrecords', 'attribute_values')
            .all()
        )
        actions = [
            {
                '_op_type': 'index',
                '_index': settings.SEARCH_INDEX_PRODUCTS,
                '_id': product.id,
                '_source': _build_product_document(product),
            }
            for product in products
        ]
        if actions:
            bulk(client, actions, refresh=False)
            count += len(actions)

    return count
