from typing import Any


def serialize_product_card(product: Any, score: float | None = None, reason: str | None = None) -> dict[str, Any]:
    stockrecord = product.stockrecords.first() if hasattr(product, 'stockrecords') else None
    price_value = None
    if stockrecord:
        # Oscar installations may expose `price` or `price_excl_tax` depending on model strategy.
        raw_price = getattr(stockrecord, 'price_excl_tax', None)
        if raw_price is None:
            raw_price = getattr(stockrecord, 'price', None)
        if raw_price is not None:
            price_value = float(raw_price)

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
        'price': price_value,
        'currency': stockrecord.price_currency if stockrecord and stockrecord.price_currency else 'USD',
        'thumbnail': image_url,
        'in_stock': bool(stockrecord and (stockrecord.num_in_stock or 0) > 0),
    }

    if score is not None:
        payload['score'] = score
    if reason:
        payload['reason'] = reason

    return payload
