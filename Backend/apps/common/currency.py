from decimal import Decimal

from django.apps import apps
from django.conf import settings


def normalize_country_code(value: str | None) -> str:
    return (value or '').strip().upper()


def normalize_currency_code(value: str | None) -> str:
    return (value or '').strip().upper()


def country_currency_map() -> dict[str, str]:
    return {
        normalize_country_code(country): normalize_currency_code(currency)
        for country, currency in getattr(settings, 'COUNTRY_CURRENCY_MAP', {}).items()
    }


def currency_rates() -> dict[str, Decimal]:
    return {
        normalize_currency_code(currency): Decimal(str(rate))
        for currency, rate in getattr(settings, 'DISPLAY_CURRENCY_RATES', {}).items()
    }


def supported_currencies() -> set[str]:
    return set(currency_rates().keys())


def currency_for_country(country_code: str | None) -> str | None:
    normalized = normalize_country_code(country_code)
    if not normalized:
        return None
    return country_currency_map().get(normalized)


def is_supported_currency(currency_code: str | None) -> bool:
    normalized = normalize_currency_code(currency_code)
    return bool(normalized and normalized in supported_currencies())


def get_customer_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    profile = getattr(user, 'customer_profile', None)
    if profile is not None:
        return profile

    CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def display_currency_for_user(user) -> str | None:
    profile = get_customer_profile(user)
    if profile is None:
        return None

    preferred_currency = normalize_currency_code(getattr(profile, 'preferred_currency', ''))
    if is_supported_currency(preferred_currency):
        return preferred_currency

    return currency_for_country(getattr(profile, 'country_code', ''))


def resolve_display_currency(request=None, user=None, country_code: str | None = None) -> str:
    if request is not None:
        params = getattr(request, 'query_params', None)
        if params is None:
            params = getattr(request, 'GET', {})

        requested_currency = normalize_currency_code(params.get('currency'))
        if is_supported_currency(requested_currency):
            return requested_currency

        requested_country = normalize_country_code(params.get('country'))
        mapped_currency = currency_for_country(requested_country)
        if mapped_currency:
            return mapped_currency

    explicit_currency = currency_for_country(country_code)
    if explicit_currency:
        return explicit_currency

    resolved_user = user
    if resolved_user is None and request is not None:
        resolved_user = getattr(request, 'user', None)

    user_currency = display_currency_for_user(resolved_user)
    if user_currency:
        return user_currency

    return normalize_currency_code(getattr(settings, 'OSCAR_DEFAULT_CURRENCY', 'USD')) or 'USD'


def convert_amount(amount, source_currency: str | None, target_currency: str | None) -> tuple[float | None, str]:
    if amount is None:
        return None, normalize_currency_code(target_currency) or normalize_currency_code(source_currency) or 'USD'

    source = normalize_currency_code(source_currency) or 'USD'
    target = normalize_currency_code(target_currency) or source

    rates = currency_rates()
    source_rate = rates.get(source)
    target_rate = rates.get(target)

    if source == target or source_rate is None or target_rate is None:
        return float(Decimal(str(amount))), source

    amount_usd = Decimal(str(amount)) / source_rate
    converted = (amount_usd * target_rate).quantize(Decimal('0.01'))
    return float(converted), target


def convert_product_payload(payload: dict, target_currency: str | None) -> dict:
    base_price = payload.get('base_price', payload.get('price'))
    base_currency = payload.get('base_currency', payload.get('currency'))
    display_price, display_currency = convert_amount(base_price, base_currency, target_currency)

    payload['base_price'] = base_price
    payload['base_currency'] = base_currency
    payload['price'] = display_price
    payload['currency'] = display_currency
    return payload
