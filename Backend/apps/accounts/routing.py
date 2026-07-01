from decimal import Decimal, InvalidOperation
from math import asin, cos, radians, sin, sqrt

from django.apps import apps
from django.conf import settings

ZERO = Decimal('0.00')
STRAIGHT_LINE_PROVIDER = 'straight_line'


def _decimal(value, *, places='0.000001') -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal(places))
    return Decimal(str(value)).quantize(Decimal(places))


def _route_coordinate(value) -> Decimal:
    precision = int(getattr(settings, 'DELIVERY_DISTANCE_CACHE_PRECISION', 4))
    precision = max(3, min(6, precision))
    return _decimal(value, places=f'0.{"0" * (precision - 1)}1')


def _money_distance(value) -> Decimal:
    if value in (None, ''):
        return ZERO
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return ZERO


def straight_line_distance_km(lat1, lon1, lat2, lon2) -> Decimal:
    radius_km = Decimal('6371.00')
    rlat1 = radians(float(lat1))
    rlon1 = radians(float(lon1))
    rlat2 = radians(float(lat2))
    rlon2 = radians(float(lon2))
    delta_lat = rlat2 - rlat1
    delta_lon = rlon2 - rlon1
    value = sin(delta_lat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(delta_lon / 2) ** 2
    distance = 2 * asin(sqrt(value)) * float(radius_km)
    return _money_distance(distance)


def route_distance(
    *,
    origin_latitude,
    origin_longitude,
    destination_latitude,
    destination_longitude,
    vehicle_type='driving',
) -> dict:
    vehicle = _vehicle_profile(vehicle_type)
    origin_lat = _route_coordinate(origin_latitude)
    origin_lon = _route_coordinate(origin_longitude)
    destination_lat = _route_coordinate(destination_latitude)
    destination_lon = _route_coordinate(destination_longitude)

    DeliveryRouteCache = apps.get_model('accounts', 'DeliveryRouteCache')
    cached = DeliveryRouteCache.objects.filter(
        provider=STRAIGHT_LINE_PROVIDER,
        vehicle_type=vehicle,
        origin_latitude=origin_lat,
        origin_longitude=origin_lon,
        destination_latitude=destination_lat,
        destination_longitude=destination_lon,
    ).first()
    if cached:
        return {
            'distance_km': cached.distance_km,
            'provider': cached.provider,
            'source': cached.source or STRAIGHT_LINE_PROVIDER,
            'cached': True,
        }

    distance = straight_line_distance_km(origin_lat, origin_lon, destination_lat, destination_lon)
    instance, _ = DeliveryRouteCache.objects.update_or_create(
        provider=STRAIGHT_LINE_PROVIDER,
        vehicle_type=vehicle,
        origin_latitude=origin_lat,
        origin_longitude=origin_lon,
        destination_latitude=destination_lat,
        destination_longitude=destination_lon,
        defaults={
            'distance_km': distance,
            'duration_seconds': 0,
            'source': STRAIGHT_LINE_PROVIDER,
            'raw_payload': {},
        },
    )
    return {
        'distance_km': instance.distance_km,
        'provider': instance.provider,
        'source': instance.source,
        'cached': False,
    }


def _vehicle_profile(vehicle_type: str) -> str:
    value = str(vehicle_type or '').strip().lower()
    if value in {'car', 'van', 'truck', 'motorcycle', 'driving'}:
        return 'driving'
    return value or 'driving'
