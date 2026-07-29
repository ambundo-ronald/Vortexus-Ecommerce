from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.common.taxes import (
    calculate_checkout_taxes,
    product_tax_profile,
    product_tax_rate,
    product_tax_status,
)


class _AttributeValues:
    def __init__(self, values):
        self.values = values

    def all(self):
        return [
            SimpleNamespace(
                attribute=SimpleNamespace(code=code),
                value_as_text=value,
                value=value,
            )
            for code, value in self.values.items()
        ]


def _product(title='Pump', **attributes):
    return SimpleNamespace(title=title, attribute_values=_AttributeValues(attributes))


def _basket(*lines):
    return SimpleNamespace(all_lines=lambda: lines)


@override_settings(
    INDUSTRIAL_TAX_RULES={
        'KE': {
            'default_rate': '0.16',
            'shipping_rate': '0.16',
            'product_profile_rates': {
                'standard': '0.16',
                'service': '0.00',
            },
            'shipping_profile_rates': {
                'pickup': '0.00',
            },
        }
    }
)
class ProductTaxRuleTests(SimpleTestCase):
    def test_taxable_product_uses_country_profile_rate(self):
        product = _product(tax_status='taxable', tax_profile='standard')

        self.assertEqual(product_tax_status(product), 'taxable')
        self.assertEqual(product_tax_profile(product), 'standard')
        self.assertEqual(product_tax_rate(product, 'KE'), Decimal('0.16'))

    def test_tax_exempt_product_has_zero_tax_rate(self):
        product = _product(tax_status='tax_exempt', tax_profile='standard')

        self.assertEqual(product_tax_status(product), 'tax_exempt')
        self.assertEqual(product_tax_rate(product, 'KE'), Decimal('0.00'))

    def test_charge_tax_false_is_treated_as_exempt_for_older_products(self):
        product = _product(charge_tax='false', tax_profile='standard')

        self.assertEqual(product_tax_status(product), 'tax_exempt')
        self.assertEqual(product_tax_rate(product, 'KE'), Decimal('0.00'))

    def test_checkout_line_breakdown_includes_exemption_metadata(self):
        exempt_product = _product(
            tax_status='tax_exempt',
            tax_profile='standard',
            tax_exemption_reason='VAT exempt supply',
        )
        taxable_product = _product(tax_status='taxable', tax_profile='standard')
        basket = _basket(
            SimpleNamespace(id=1, product_id=10, product=exempt_product, quantity=1, line_price_excl_tax=Decimal('100.00'), line_price_incl_tax=None),
            SimpleNamespace(id=2, product_id=20, product=taxable_product, quantity=1, line_price_excl_tax=Decimal('100.00'), line_price_incl_tax=None),
        )

        taxes = calculate_checkout_taxes(Decimal('200.00'), Decimal('0.00'), 'KE', basket=basket)

        self.assertEqual(taxes['merchandise_tax'], 16.0)
        self.assertEqual(taxes['line_breakdown'][0]['tax_status'], 'tax_exempt')
        self.assertEqual(taxes['line_breakdown'][0]['line_tax'], 0.0)
        self.assertEqual(taxes['line_breakdown'][0]['exemption_reason'], 'VAT exempt supply')
        self.assertEqual(taxes['line_breakdown'][1]['tax_status'], 'taxable')
        self.assertEqual(taxes['line_breakdown'][1]['line_tax'], 16.0)
