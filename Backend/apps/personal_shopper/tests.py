from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .discounts import sync_shopper_discount
from .models import ShopperList


class ShopperHubSecurityTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='shopper', email='shopper@example.com', password='test', is_staff=True)
        self.customer = User.objects.create_user(username='customer', email='customer@example.com', password='test')
        self.other_customer = User.objects.create_user(username='other', email='other@example.com', password='test')
        self.shopper_list = ShopperList.objects.create(
            customer=self.customer,
            created_by=self.staff,
            title='Pump setup',
            status=ShopperList.Status.SHARED,
        )
        self.url = reverse('shopper-hub', kwargs={'token': self.shopper_list.share_token})

    def test_hub_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hub_rejects_another_customer(self):
        self.client.force_authenticate(self.other_customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_view_and_status_is_recorded(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shopper_list.refresh_from_db()
        self.assertEqual(self.shopper_list.status, ShopperList.Status.VIEWED)
        self.assertIsNotNone(self.shopper_list.viewed_at)

    def test_expired_list_is_unavailable(self):
        self.shopper_list.expires_at = timezone.now() - timedelta(minutes=1)
        self.shopper_list.save(update_fields=['expires_at'])
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_published_discount_generates_customer_scoped_voucher(self):
        self.shopper_list.discount_percentage = 12.5
        self.shopper_list.save(update_fields=['discount_percentage'])
        voucher = sync_shopper_discount(self.shopper_list)
        self.shopper_list.refresh_from_db()

        self.assertIsNotNone(voucher)
        self.assertTrue(voucher.code.startswith('HUB-'))
        self.assertEqual(voucher.offers.get().benefit.value, 12.5)
        self.assertEqual(self.shopper_list.discount_voucher_id, voucher.id)

        self.client.force_authenticate(self.other_customer)
        response = self.client.post(reverse('checkout-vouchers'), {'code': voucher.code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('another customer', str(response.data))

    def test_staff_can_duplicate_list_for_another_customer_with_fresh_share_credentials(self):
        self.shopper_list.discount_percentage = 10
        self.shopper_list.note = 'Use the same setup.'
        self.shopper_list.save(update_fields=['discount_percentage', 'note'])
        sync_shopper_discount(self.shopper_list)
        self.shopper_list.refresh_from_db()

        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse('admin-shopper-list-duplicate', kwargs={'list_id': self.shopper_list.id}),
            {'customer_id': self.other_customer.id, 'status': ShopperList.Status.SHARED},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        duplicate = ShopperList.objects.get(id=response.data['shopper_list']['id'])
        self.assertEqual(duplicate.customer_id, self.other_customer.id)
        self.assertEqual(duplicate.note, self.shopper_list.note)
        self.assertEqual(duplicate.discount_percentage, self.shopper_list.discount_percentage)
        self.assertNotEqual(duplicate.share_token, self.shopper_list.share_token)
        self.assertNotEqual(duplicate.discount_voucher_id, self.shopper_list.discount_voucher_id)
        self.assertNotEqual(duplicate.discount_voucher.code, self.shopper_list.discount_voucher.code)
