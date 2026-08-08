import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Any

from django.apps import apps
from django.conf import settings

from apps.common.catalog import product_brand
from apps.common.products import serialize_product_card, stockrecord_count


GOOGLE_MERCHANT_FEED_HEADERS = [
    'id',
    'title',
    'description',
    'availability',
    'availability_date',
    'expiration_date',
    'link',
    'mobile_link',
    'image_link',
    'price',
    'sale_price',
    'sale_price_effective_date',
    'identifier_exists',
    'gtin',
    'mpn',
    'brand',
    'product_highlight',
    'product_detail',
    'additional_image_link',
    'condition',
    'adult',
    'color',
    'size',
    'size_type',
    'size_system',
    'gender',
    'material',
    'pattern',
    'age_group',
    'multipack',
    'is bundle',
    'unit_pricing_measure',
    'unit_pricing_base_measure',
    'energy_efficiency_class',
    'min_energy_efficiency_class',
    'max_energy_efficiency',
    'item_group_id',
    'video_link',
    'virtual_model_link',
    'cost_of_goods_sold',
]


def google_merchant_product_queryset():
    Product = apps.get_model('catalogue', 'Product')
    return (
        Product.objects.filter(is_public=True)
        .exclude(structure='parent')
        .prefetch_related('stockrecords', 'categories', 'images', 'attribute_values__attribute')
        .order_by('id')
    )


def build_google_merchant_feed_rows(*, tax_country_code: str = 'KE') -> list[dict[str, str]]:
    rows = []
    for product in google_merchant_product_queryset():
        row = build_google_merchant_feed_row(product, tax_country_code=tax_country_code)
        if row:
            rows.append(row)
    return rows


def build_google_merchant_feed_row(product: Any, *, tax_country_code: str = 'KE') -> dict[str, str] | None:
    card = serialize_product_card(product, include_tax=True, tax_country_code=tax_country_code)
    price = _format_price(card.get('price_incl_tax') or card.get('price'), card.get('currency') or 'KES')
    image_link = _absolute_image_url(product)
    description = _plain_text(getattr(product, 'description', ''))
    title = _plain_text(getattr(product, 'title', ''))
    if not title or not description or not price or not image_link:
        return None

    upc = str(getattr(product, 'upc', '') or '').strip()
    brand = product_brand(product) or getattr(settings, 'OSCAR_SHOP_NAME', 'Reesolmart')
    categories = list(product.categories.all()) if hasattr(product, 'categories') else []
    product_type = _product_type(categories)
    additional_images = _additional_image_urls(product)
    stock_available = sum(stockrecord_count(stockrecord) for stockrecord in product.stockrecords.all()) > 0

    row = {header: '' for header in GOOGLE_MERCHANT_FEED_HEADERS}
    row.update(
        {
            'id': (upc or f'product-{product.id}')[:50],
            'title': title[:150],
            'description': description[:5000],
            'availability': 'in_stock' if stock_available else 'out_of_stock',
            'link': f"{settings.STOREFRONT_BASE_URL.rstrip('/')}/products/{product.id}",
            'mobile_link': f"{settings.STOREFRONT_BASE_URL.rstrip('/')}/products/{product.id}",
            'image_link': image_link,
            'price': price,
            'identifier_exists': 'yes' if upc else 'no',
            'mpn': upc[:70],
            'brand': brand[:70],
            'product_highlight': product_type[:150],
            'product_detail': f'Product type: Category: {product_type[:500]}' if product_type else '',
            'additional_image_link': ','.join(additional_images[:10]),
            'condition': 'new',
            'adult': 'no',
        }
    )
    return row


def render_google_merchant_feed_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=GOOGLE_MERCHANT_FEED_HEADERS, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def _format_price(amount: Any, currency: str) -> str:
    if amount is None:
        return ''
    try:
        value = Decimal(str(amount)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return ''
    return f'{value} {str(currency or "KES").upper()}'


def _plain_text(value: Any) -> str:
    return ' '.join(str(value or '').split())


def _product_type(categories: list[Any]) -> str:
    if not categories:
        return ''
    categories.sort(key=lambda category: (getattr(category, 'depth', 0), getattr(category, 'name', '')))
    return ' > '.join(category.name for category in categories if getattr(category, 'name', ''))


def _absolute_image_url(product: Any) -> str:
    try:
        image = product.primary_image()
    except TypeError:
        image = product.primary_image
    except Exception:
        image = None
    return _absolute_image_file_url(getattr(image, 'original', None))


def _additional_image_urls(product: Any) -> list[str]:
    urls = []
    try:
        images = list(product.images.all().order_by('display_order', 'id'))
    except Exception:
        images = []
    for image in images:
        url = _absolute_image_file_url(getattr(image, 'original', None))
        if url and url not in urls:
            urls.append(url)
    return urls[1:]


def _absolute_image_file_url(file_field: Any) -> str:
    if not file_field:
        return ''
    url = getattr(file_field, 'url', '') or ''
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    base_url = settings.BACKEND_PUBLIC_BASE_URL.rstrip('/')
    return f'{base_url}{url if url.startswith("/") else f"/{url}"}'
