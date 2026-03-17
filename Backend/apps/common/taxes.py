from decimal import Decimal

ZERO = Decimal('0.00')

TAX_RATES_BY_COUNTRY = {
    'KE': Decimal('0.16'),
    'UG': Decimal('0.18'),
    'TZ': Decimal('0.18'),
    'RW': Decimal('0.18'),
    'ET': Decimal('0.15'),
}


def normalize_country_code(country_code: str | None) -> str:
    return (country_code or '').strip().upper()


def tax_rate_for_country(country_code: str | None) -> Decimal | None:
    normalized = normalize_country_code(country_code)
    if not normalized:
        return None
    return TAX_RATES_BY_COUNTRY.get(normalized)


def calculate_tax_amount(amount, rate: Decimal | None) -> Decimal:
    if rate is None or amount is None:
        return ZERO
    return (Decimal(str(amount)) * rate).quantize(Decimal('0.01'))


def calculate_checkout_taxes(subtotal, shipping_charge, country_code: str | None) -> dict:
    rate = tax_rate_for_country(country_code)
    merchandise_tax = calculate_tax_amount(subtotal, rate)
    shipping_tax = calculate_tax_amount(shipping_charge, rate)
    total_tax = (merchandise_tax + shipping_tax).quantize(Decimal('0.01'))

    return {
        'known': rate is not None,
        'country_code': normalize_country_code(country_code),
        'rate': float(rate) if rate is not None else None,
        'merchandise_tax': float(merchandise_tax),
        'shipping_tax': float(shipping_tax),
        'total_tax': float(total_tax),
    }
