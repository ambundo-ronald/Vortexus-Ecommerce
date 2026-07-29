from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import CustomerProfile
from apps.payments.models import PaymentProviderConfiguration


class CashOnDeliveryStorefrontStateTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='cod-customer',
            email='cod-customer@example.com',
            password='password',
        )
        self.profile, _ = CustomerProfile.objects.get_or_create(user=self.user)
        PaymentProviderConfiguration.objects.create(
            provider='cash_on_delivery',
            is_enabled=True,
            public_config={'requires_customer_approval': True, 'prompt_before_dispatch': True},
        )

    def test_account_me_exposes_cash_on_delivery_permission(self):
        self.profile.cash_on_delivery_allowed = True
        self.profile.save(update_fields=['cash_on_delivery_allowed'])
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('account-profile'))

        self.assertEqual(response.status_code, 200)
        user_payload = response.data['user']
        self.assertTrue(user_payload['cash_on_delivery_allowed'])
        self.assertTrue(user_payload['payment_permissions']['cash_on_delivery_allowed'])
        self.assertTrue(user_payload['payment_permissions']['cash_on_delivery_available'])

    def test_payment_methods_include_cash_on_delivery_after_customer_approval(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('checkout-payment-methods'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('cash_on_delivery', {method['code'] for method in response.data['results']})

        self.profile.cash_on_delivery_allowed = True
        self.profile.save(update_fields=['cash_on_delivery_allowed'])

        response = self.client.get(reverse('checkout-payment-methods'))

        self.assertEqual(response.status_code, 200)
        methods = {method['code']: method for method in response.data['results']}
        self.assertIn('cash_on_delivery', methods)
        self.assertTrue(methods['cash_on_delivery']['cash_on_delivery']['customer_approved'])
