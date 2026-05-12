from typing import Any

from apps.common.currency import convert_product_payload


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
    return 'USD'


def stockrecord_count(stockrecord: Any) -> int:
    if not stockrecord:
        return 0
    return int(getattr(stockrecord, 'num_in_stock', 0) or 0)


def serialize_product_card(
    product: Any,
    score: float | None = None,
    reason: str | None = None,
    display_currency: str | None = None,
) -> dict[str, Any]:
    stockrecord = product.stockrecords.first() if hasattr(product, 'stockrecords') else None
    base_price = stockrecord_price(stockrecord)
    base_currency = stockrecord_currency(stockrecord)
    stock_count = stockrecord_count(stockrecord)

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
        'sku': product.upc,
        'price': base_price,
        'currency': base_currency,
        'base_price': base_price,
        'base_currency': base_currency,
        'thumbnail': image_url,
        'in_stock': stock_count > 0,
        'stock_count': stock_count,
        'num_in_stock': stock_count,
        'rating': _product_rating(product),
        'review_count': _product_review_count(product),
    }

    if score is not None:
        payload['score'] = score
    if reason:
        payload['reason'] = reason

    return convert_product_payload(payload, display_currency)


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
    return 0
