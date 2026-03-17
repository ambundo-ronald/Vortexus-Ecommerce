from decimal import Decimal, InvalidOperation

from django.conf import settings

ZERO = Decimal('0.00')


def normalize_country_code(country_code: str | None) -> str:
    return (country_code or '').strip().upper()


def _decimal(value, default: Decimal = ZERO) -> Decimal:
    if value in (None, ''):
        return default
    if isinstance(value, Decimal):
        return value.quantize(Decimal('0.01'))
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _rules_for_country(country_code: str | None) -> dict:
    rules = getattr(settings, 'INDUSTRIAL_TAX_RULES', {})
    return rules.get(normalize_country_code(country_code), {})


def tax_rate_for_country(country_code: str | None) -> Decimal | None:
    rules = _rules_for_country(country_code)
    if not rules:
        return None
    return _decimal(rules.get('default_rate'), default=ZERO)


def shipping_tax_rate(country_code: str | None, shipping_profile: str | None = None) -> Decimal | None:
    rules = _rules_for_country(country_code)
    if not rules:
        return None
    shipping_profile = (shipping_profile or '').strip().lower()
    profile_rates = rules.get('shipping_profile_rates', {})
    if shipping_profile and shipping_profile in profile_rates:
        return _decimal(profile_rates[shipping_profile], default=ZERO)
    return _decimal(rules.get('shipping_rate', rules.get('default_rate')), default=ZERO)


def product_tax_profile(product) -> str:
    for attribute_value in getattr(product, 'attribute_values', []).all():
        attribute = getattr(attribute_value, 'attribute', None)
        if not attribute:
            continue
        if attribute.code == 'tax_profile':
            value = (attribute_value.value_as_text or '').strip().lower()
            if value:
                return value

    title = (getattr(product, 'title', '') or '').lower()
    if any(token in title for token in ('chemical', 'chlorine', 'media', 'resin')):
        return 'water_treatment_chemical'
    if any(token in title for token in ('installation service', 'maintenance service', 'inspection service')):
        return 'service'
    if any(token in title for token in ('accessory', 'fitting', 'controller', 'sensor')):
        return 'accessory'
    if any(token in title for token in ('borehole', 'treatment system', 'dosing plant', 'tank')):
        return 'project'
    return 'standard'


def product_tax_rate(product, country_code: str | None) -> Decimal | None:
    rules = _rules_for_country(country_code)
    if not rules:
        return None

    profile = product_tax_profile(product)
    profile_rates = rules.get('product_profile_rates', {})
    if profile in profile_rates:
        return _decimal(profile_rates[profile], default=ZERO)

    return _decimal(rules.get('default_rate'), default=ZERO)


def calculate_tax_amount(amount, rate: Decimal | None) -> Decimal:
    if rate is None or amount is None:
        return ZERO
    return (Decimal(str(amount)) * rate).quantize(Decimal('0.01'))


def calculate_checkout_taxes(
    subtotal,
    shipping_charge,
    country_code: str | None,
    *,
    basket=None,
    shipping_method=None,
) -> dict:
    normalized_country = normalize_country_code(country_code)
    if not basket:
        rate = tax_rate_for_country(normalized_country)
        merchandise_tax = calculate_tax_amount(subtotal, rate)
        shipping_tax = calculate_tax_amount(shipping_charge, shipping_tax_rate(normalized_country))
        total_tax = (merchandise_tax + shipping_tax).quantize(Decimal('0.01'))
        return {
            'known': rate is not None,
            'country_code': normalized_country,
            'default_rate': float(rate) if rate is not None else None,
            'shipping_rate': float(shipping_tax_rate(normalized_country)) if shipping_tax_rate(normalized_country) is not None else None,
            'merchandise_tax': float(merchandise_tax),
            'shipping_tax': float(shipping_tax),
            'total_tax': float(total_tax),
            'line_breakdown': [],
        }

    line_breakdown = []
    merchandise_tax = ZERO
    item_count = 0

    for line in basket.all_lines():
        line_subtotal = Decimal(str(line.line_price_excl_tax or line.line_price_incl_tax or ZERO))
        rate = product_tax_rate(line.product, normalized_country)
        tax_amount = calculate_tax_amount(line_subtotal, rate)
        merchandise_tax += tax_amount
        item_count += int(line.quantity or 0)
        line_breakdown.append(
            {
                'line_id': line.id,
                'product_id': line.product_id,
                'quantity': int(line.quantity or 0),
                'tax_profile': product_tax_profile(line.product),
                'tax_rate': float(rate) if rate is not None else None,
                'line_subtotal': float(line_subtotal.quantize(Decimal('0.01'))),
                'line_tax': float(tax_amount),
            }
        )

    shipping_profile = getattr(shipping_method, 'method_type', '') if shipping_method else ''
    shipping_rate = shipping_tax_rate(normalized_country, shipping_profile)
    shipping_tax = calculate_tax_amount(shipping_charge, shipping_rate)
    total_tax = (merchandise_tax + shipping_tax).quantize(Decimal('0.01'))
    default_rate = tax_rate_for_country(normalized_country)

    return {
        'known': default_rate is not None,
        'country_code': normalized_country,
        'default_rate': float(default_rate) if default_rate is not None else None,
        'shipping_rate': float(shipping_rate) if shipping_rate is not None else None,
        'shipping_profile': shipping_profile or '',
        'item_count': item_count,
        'merchandise_tax': float(merchandise_tax.quantize(Decimal('0.01'))),
        'shipping_tax': float(shipping_tax.quantize(Decimal('0.01'))),
        'total_tax': float(total_tax),
        'line_breakdown': line_breakdown,
    }
