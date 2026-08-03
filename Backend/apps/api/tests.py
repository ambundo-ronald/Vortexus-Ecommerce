from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from oscar.core.loading import get_model
from rest_framework import status
from rest_framework.test import APITestCase


class StorefrontProductVisibilityTests(APITestCase):
    def setUp(self):
        ProductClass = get_model('catalogue', 'ProductClass')
        Product = get_model('catalogue', 'Product')

        product_class, _ = ProductClass.objects.get_or_create(name='Test products')
        self.active_product = Product.objects.create(
            product_class=product_class,
            structure=Product.STANDALONE,
            upc='ACTIVE-SKU',
            title='Active storefront product',
            slug='active-storefront-product',
            is_public=True,
        )
        self.draft_product = Product.objects.create(
            product_class=product_class,
            structure=Product.STANDALONE,
            upc='DRAFT-SKU',
            title='Draft storefront product',
            slug='draft-storefront-product',
            is_public=False,
        )
        StockRecord = get_model('partner', 'StockRecord')
        StockRecord.objects.create(
            product=self.active_product,
            partner_sku='ACTIVE-SKU',
            price_currency='KES',
            price=Decimal('100.00'),
            num_in_stock=10,
        )
        ProductTaxConfiguration = apps.get_model('accounts', 'ProductTaxConfiguration')
        ProductTaxConfiguration.objects.create(product=self.active_product, status='taxable')
        self.staff_user = get_user_model().objects.create_superuser(
            username='storefront-admin',
            email='storefront-admin@example.com',
            password='test-password-123',
        )

    def test_storefront_product_list_hides_drafts_even_for_staff(self):
        self.client.force_authenticate(self.staff_user)

        response = self.client.get(reverse('catalog-products'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.active_product.id, product_ids)
        self.assertNotIn(self.draft_product.id, product_ids)

    def test_storefront_product_detail_hides_draft_even_for_staff(self):
        self.client.force_authenticate(self.staff_user)

        response = self.client.get(reverse('catalog-product-detail', kwargs={'product_id': self.draft_product.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(INDUSTRIAL_TAX_RULES={'KE': {'default_rate': '0.16'}})
    def test_storefront_product_list_uses_tax_inclusive_price(self):
        response = self.client.get(reverse('catalog-products'), {'country': 'KE'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = next(item for item in response.data['results'] if item['id'] == self.active_product.id)
        self.assertEqual(product['price'], 116.0)
        self.assertEqual(product['base_price'], 116.0)
        self.assertEqual(product['price_excl_tax'], 100.0)
        self.assertEqual(product['price_incl_tax'], 116.0)
        self.assertEqual(product['tax_amount'], 16.0)
        self.assertTrue(product['prices_include_tax'])
