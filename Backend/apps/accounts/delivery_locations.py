from decimal import Decimal, InvalidOperation

from django.apps import apps


DELIVERY_LOCATION_SESSION_KEY = 'checkout_delivery_location'


def clean_coordinate(value, *, min_value: Decimal, max_value: Decimal) -> Decimal | None:
    if value in (None, ''):
        return None
    try:
        coordinate = Decimal(str(value)).quantize(Decimal('0.000001'))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if coordinate < min_value or coordinate > max_value:
        return None
    return coordinate


def clean_location_payload(data: dict | None) -> dict | None:
    data = data or {}
    latitude = clean_coordinate(data.get('latitude'), min_value=Decimal('-90'), max_value=Decimal('90'))
    longitude = clean_coordinate(data.get('longitude'), min_value=Decimal('-180'), max_value=Decimal('180'))
    if latitude is None or longitude is None:
        return None
    confidence = None
    if data.get('confidence') not in (None, ''):
        try:
            confidence = Decimal(str(data.get('confidence'))).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError, ValueError):
            confidence = None
        if confidence is not None:
            confidence = max(Decimal('0.00'), min(Decimal('1.00'), confidence))
    return {
        'latitude': latitude,
        'longitude': longitude,
        'label': str(data.get('label') or '').strip()[:120],
        'source': str(data.get('source') or '').strip()[:32],
        'provider': str(data.get('provider') or '').strip()[:32],
        'place_id': str(data.get('place_id') or '').strip()[:128],
        'formatted_address': str(data.get('formatted_address') or '').strip()[:255],
        'confidence': confidence,
    }


def serialize_location(location) -> dict | None:
    if not location:
        return None
    return {
        'latitude': float(location.latitude),
        'longitude': float(location.longitude),
        'label': location.label or '',
        'source': location.source or '',
        'provider': location.provider or '',
        'place_id': location.place_id or '',
        'formatted_address': location.formatted_address or '',
        'confidence': float(location.confidence) if location.confidence is not None else None,
    }


def location_for_user_address(address) -> dict | None:
    if not address:
        return None
    try:
        return serialize_location(address.delivery_location)
    except Exception:
        return None


def location_for_shipping_address(address) -> dict | None:
    if not address:
        return None
    try:
        return serialize_location(address.delivery_location)
    except Exception:
        return None


def upsert_user_address_location(address, payload: dict | None):
    location = clean_location_payload(payload)
    if not address:
        return None

    DeliveryLocation = apps.get_model('accounts', 'DeliveryLocation')
    if location is None:
        DeliveryLocation.objects.filter(user_address=address).delete()
        return None

    instance, _ = DeliveryLocation.objects.update_or_create(
        user_address=address,
        defaults={**location, 'shipping_address': None},
    )
    return instance


def upsert_shipping_address_location(address, payload: dict | None):
    location = clean_location_payload(payload)
    if not address or location is None:
        return None

    DeliveryLocation = apps.get_model('accounts', 'DeliveryLocation')
    instance, _ = DeliveryLocation.objects.update_or_create(
        shipping_address=address,
        defaults={**location, 'user_address': None},
    )
    return instance


def store_session_location(request, payload: dict | None):
    location = clean_location_payload(payload)
    if location is None:
        request.session.pop(DELIVERY_LOCATION_SESSION_KEY, None)
    else:
        request.session[DELIVERY_LOCATION_SESSION_KEY] = {
            'latitude': str(location['latitude']),
            'longitude': str(location['longitude']),
            'label': location['label'],
            'source': location['source'],
        }
    request.session.modified = True


def get_session_location(request) -> dict | None:
    return clean_location_payload(request.session.get(DELIVERY_LOCATION_SESSION_KEY))
