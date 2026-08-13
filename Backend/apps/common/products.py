from typing import Any
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from apps.common.catalog import brand_slug, product_brand
from apps.common.currency import convert_amount, convert_product_payload, default_currency
from apps.common.taxes import calculate_tax_amount, product_tax_rate, product_tax_status


def _slugify_segment(value: Any) -> str:
    return slugify(str(value or '').strip())


def product_slug(product: Any) -> str:
    source = (
        getattr(product, 'slug', None)
        or getattr(product, 'title', None)
        or getattr(product, 'upc', None)
        or getattr(product, 'id', None)
        or ''
    )
    return _slugify_segment(source)


def product_url(product: Any) -> str:
    product_id = getattr(product, 'id', None)
    slug = product_slug(product)
    suffix = f'{slug}-{product_id}' if product_id and slug else str(product_id or slug)

    categories = list(product.categories.all()) if hasattr(product, 'categories') else []
    primary_category = categories[0] if categories else None
    brand = product_brand(product)
    segments = [
        getattr(primary_category, 'slug', '') if primary_category else '',
        brand_slug(brand),
        suffix,
    ]
    path = '/'.join(segment for segment in segments if segment)
    return f'/products/{path}' if path else '/catalog'


def stockrecord_price(stockrecord: Any) -> float | None:
    if not stockrecord:
        return None

    # Oscar installations may expose `price` or `price_excl_tax` depending on strategy/model.
    raw_price = getattr(stockrecord, 'price_excl_tax', None)
    if raw_price is None:
        raw_price = getattr(stockrecord, 'price', None)

    if raw_price is None:
        return None

    return float(raw_price)


def stockrecord_currency(stockrecord: Any) -> str:
    if stockrecord and getattr(stockrecord, 'price_currency', None):
        return stockrecord.price_currency
    return default_currency()


def stockrecord_previous_price(stockrecord: Any) -> float | None:
    if not stockrecord:
        return None

    try:
        snapshot = stockrecord.price_snapshot
    except ObjectDoesNotExist:
        return None

    if not snapshot or snapshot.previous_price is None:
        return None

    return float(snapshot.previous_price)


def stockrecord_previous_currency(stockrecord: Any) -> str:
    if not stockrecord:
        return default_currency()

    try:
        snapshot = stockrecord.price_snapshot
    except ObjectDoesNotExist:
        return stockrecord_currency(stockrecord)

    if snapshot and snapshot.previous_currency:
        return snapshot.previous_currency
    return stockrecord_currency(stockrecord)


def stockrecord_count(stockrecord: Any) -> int:
    if not stockrecord:
        return 0

    net_stock_level = getattr(stockrecord, 'net_stock_level', None)
    if callable(net_stock_level):
        net_stock_level = net_stock_level()
    if net_stock_level is not None:
        return max(0, int(net_stock_level or 0))

    num_in_stock = int(getattr(stockrecord, 'num_in_stock', 0) or 0)
    num_allocated = int(getattr(stockrecord, 'num_allocated', 0) or 0)
    return max(0, num_in_stock - num_allocated)


def _money(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal('0.01'))


def _taxed_price(product: Any, amount: Any, country_code: str | None) -> tuple[float | None, float, float | None]:
    base = _money(amount)
    if base is None:
        return None, 0.0, None

    rate = product_tax_rate(product, country_code)
    tax_amount = calculate_tax_amount(base, rate)
    inclusive = (base + tax_amount).quantize(Decimal('0.01'))
    return float(inclusive), float(tax_amount), float(rate) if rate is not None else None


def _convert_extra_price_fields(payload: dict[str, Any], display_currency: str | None) -> dict[str, Any]:
    field_pairs = (
        ('base_price_excl_tax', 'price_excl_tax'),
        ('base_price_incl_tax', 'price_incl_tax'),
        ('base_tax_amount', 'tax_amount'),
        ('base_previous_price_excl_tax', 'previous_price_excl_tax'),
        ('base_previous_price_incl_tax', 'previous_price_incl_tax'),
    )
    for base_field, display_field in field_pairs:
        converted, _ = convert_amount(payload.get(base_field), payload.get('base_currency'), display_currency)
        payload[display_field] = converted
    return payload


def product_stock_totals(product: Any) -> dict[str, int]:
    stockrecords = list(product.stockrecords.all()) if hasattr(product, 'stockrecords') else []
    return {
        'available': sum(stockrecord_count(stockrecord) for stockrecord in stockrecords),
        'on_hand': sum(int(getattr(stockrecord, 'num_in_stock', 0) or 0) for stockrecord in stockrecords),
        'allocated': sum(int(getattr(stockrecord, 'num_allocated', 0) or 0) for stockrecord in stockrecords),
    }


def serialize_product_card(
    product: Any,
    score: float | None = None,
    reason: str | None = None,
    display_currency: str | None = None,
    include_tax: bool = False,
    tax_country_code: str | None = None,
) -> dict[str, Any]:
    stockrecord = product.stockrecords.first() if hasattr(product, 'stockrecords') else None
    base_price = stockrecord_price(stockrecord)
    base_currency = stockrecord_currency(stockrecord)
    base_previous_price = stockrecord_previous_price(stockrecord)
    base_previous_currency = stockrecord_previous_currency(stockrecord)
    base_price_incl_tax, base_tax_amount, tax_rate = _taxed_price(product, base_price, tax_country_code)
    base_previous_price_incl_tax, _, _ = _taxed_price(product, base_previous_price, tax_country_code)
    display_base_price = base_price_incl_tax if include_tax else base_price
    display_previous_price = base_previous_price_incl_tax if include_tax else base_previous_price
    stock_count = product_stock_totals(product)['available']
    brand = product_brand(product)
    categories = list(product.categories.all()) if hasattr(product, 'categories') else []
    primary_category = categories[0] if categories else None

    image_url = ''
    try:
        image = product.primary_image()
        if image and getattr(image, 'original', None):
            image_url = image.original.url or ''
    except Exception:
        image_url = ''

    payload: dict[str, Any] = {
        'id': product.id,
        'title': product.title,
        'slug': product_slug(product),
        'url': product_url(product),
        'sku': product.upc,
        'price': display_base_price,
        'currency': base_currency,
        'base_price': display_base_price,
        'base_currency': base_currency,
        'price_excl_tax': base_price,
        'price_incl_tax': base_price_incl_tax,
        'base_price_excl_tax': base_price,
        'base_price_incl_tax': base_price_incl_tax,
        'tax_amount': base_tax_amount,
        'base_tax_amount': base_tax_amount,
        'tax_rate': tax_rate,
        'tax_status': product_tax_status(product),
        'tax_country_code': tax_country_code or '',
        'prices_include_tax': include_tax,
        'previous_price': display_previous_price,
        'previous_currency': base_previous_currency,
        'base_previous_price': display_previous_price,
        'base_previous_currency': base_previous_currency,
        'previous_price_excl_tax': base_previous_price,
        'previous_price_incl_tax': base_previous_price_incl_tax,
        'base_previous_price_excl_tax': base_previous_price,
        'base_previous_price_incl_tax': base_previous_price_incl_tax,
        'thumbnail': image_url,
        'brand': brand,
        'brand_slug': brand_slug(brand),
        'category': getattr(primary_category, 'name', '') if primary_category else '',
        'category_slug': getattr(primary_category, 'slug', '') if primary_category else '',
        'categories': [
            {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
            }
            for category in categories
        ],
        'in_stock': stock_count > 0,
        'stock_count': stock_count,
        'num_in_stock': stock_count,
        'rating': _product_rating(product),
        'review_count': _product_review_count(product),
        'updated_at': getattr(product, 'date_updated', None),
    }

    if score is not None:
        payload['score'] = score
    if reason:
        payload['reason'] = reason

    payload = convert_product_payload(payload, display_currency)
    return _convert_extra_price_fields(payload, display_currency)


def _product_rating(product: Any) -> float | None:
    annotated_average = getattr(product, 'average_review_score', None)
    if annotated_average is not None:
        return float(annotated_average)
    rating = getattr(product, 'rating', None)
    return float(rating) if rating is not None else None


def _product_review_count(product: Any) -> int:
    annotated_count = getattr(product, 'review_count', None)
    if annotated_count is not None:
        return int(annotated_count or 0)

    try:
        return int(product.num_approved_reviews or 0)
    except (AttributeError, TypeError, ValueError):
        return 0
