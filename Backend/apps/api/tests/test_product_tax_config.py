from django.apps import apps
from django.test import TestCase

from apps.api.serializers import ProductWriteSerializer


class ProductTaxConfigurationSerializerTests(TestCase):
    def _create_product(self, tax_status='tax_exempt'):
        serializer = ProductWriteSerializer(
            data={
                'upc': f'TAX-{tax_status}',
                'title': f'{tax_status} product',
                'price': '100.00',
                'currency': 'KES',
                'num_in_stock': 5,
                'tax_status': tax_status,
                'attributes': {
                    'brand': 'Reesolmart',
                    'flow_rate': '10 lpm',
                },
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_product_tax_status_is_saved_outside_product_attributes(self):
        product = self._create_product('tax_exempt')
        ProductAttributeValue = apps.get_model('catalogue', 'ProductAttributeValue')

        self.assertEqual(product.tax_configuration.status, 'tax_exempt')
        self.assertFalse(
            ProductAttributeValue.objects.filter(
                product=product,
                attribute__code__in=['tax_status', 'charge_tax', 'tax_profile', 'tax_exemption_reason'],
            ).exists()
        )
        self.assertTrue(ProductAttributeValue.objects.filter(product=product, attribute__code='brand').exists())

    def test_product_tax_status_updates_tax_configuration_only(self):
        product = self._create_product('taxable')

        serializer = ProductWriteSerializer(instance=product, data={'tax_status': 'zero_rated'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        updated.tax_configuration.refresh_from_db()
        self.assertEqual(updated.tax_configuration.status, 'zero_rated')
