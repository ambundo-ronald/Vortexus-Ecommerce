from typing import Any

from celery import shared_task
from django.apps import apps
from django.conf import settings

from apps.common.clients import get_opensearch_client
from apps.common.products import stockrecord_currency, stockrecord_price


def _build_product_document(product: Any) -> dict[str, Any]:
    stockrecord = product.stockrecords.first()

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
        'attributes_text': attributes_text,
    }


@shared_task
def index_product_for_search(product_id: int) -> bool:
    Product = apps.get_model('catalogue', 'Product')
    product = (
        Product.objects.filter(id=product_id, is_public=True)
        .prefetch_related('categories', 'stockrecords', 'attribute_values')
        .first()
    )
    if not product:
        return False

    client = get_opensearch_client()
    document = _build_product_document(product)
    client.index(index=settings.SEARCH_INDEX_PRODUCTS, id=product.id, body=document, refresh=False)
    return True


@shared_task
def reindex_all_products(batch_size: int = 500) -> int:
    Product = apps.get_model('catalogue', 'Product')
    product_ids = list(Product.objects.filter(is_public=True).values_list('id', flat=True))

    count = 0
    for product_id in product_ids:
        if index_product_for_search(product_id):
            count += 1

    return count
