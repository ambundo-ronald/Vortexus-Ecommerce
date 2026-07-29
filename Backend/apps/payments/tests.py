from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.api.payment_serializers import PesapalNotificationSerializer
from apps.accounts.models import CustomerProfile

from .models import PaymentEvent, PaymentProviderConfiguration, PaymentReconciliation, PaymentSession
from .pesapal import PesapalGatewayError, handle_transaction_status, request_refund
from .services import (
    _payment_method_capabilities,
    available_payment_methods,
    customer_can_use_cash_on_delivery,
    get_payment_method,
    payment_reconciliation,
    sync_payment_reconciliation,
)


class PaymentMethodCapabilityTests(SimpleTestCase):
    @override_settings(PESAPAL_BASE_URL='https://cybqa.pesapal.com/pesapalv3/api')
    @patch('apps.payments.services.get_payment_setting', return_value='https://cybqa.pesapal.com/pesapalv3/api')
    def test_pesapal_sandbox_is_exposed_to_the_storefront(self, _get_payment_setting):
        self.assertEqual(
            _payment_method_capabilities('pesapal', 'pesapal'),
            {'flow': 'redirect', 'is_sandbox': True},
        )

    @override_settings(CARD_SANDBOX_ENABLED=True)
    def test_card_sandbox_is_exposed_to_the_storefront(self):
        self.assertEqual(
            _payment_method_capabilities('credit_card', 'card'),
            {'flow': 'card_token', 'is_sandbox': True},
        )


class CashOnDeliveryAvailabilityTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='customer', email='customer@example.com', password='password')
        self.staff = self.User.objects.create_user(username='staff', email='staff@example.com', password='password', is_staff=True)
        CustomerProfile.objects.create(user=self.user)
        PaymentProviderConfiguration.objects.create(
            provider='cash_on_delivery',
            is_enabled=True,
            public_config={'requires_customer_approval': True, 'prompt_before_dispatch': True},
        )

    def _method_codes(self, user=None):
        return {method['code'] for method in available_payment_methods(user=user)}

    def test_cash_on_delivery_is_not_enabled_without_provider_config(self):
        PaymentProviderConfiguration.objects.filter(provider='cash_on_delivery').delete()

        self.user.customer_profile.cash_on_delivery_allowed = True
        self.user.customer_profile.save(update_fields=['cash_on_delivery_allowed'])

        self.assertNotIn('cash_on_delivery', self._method_codes(self.user))

    def test_cash_on_delivery_requires_customer_approval(self):
        self.assertFalse(customer_can_use_cash_on_delivery(self.user))
        self.assertNotIn('cash_on_delivery', self._method_codes(self.user))

        self.user.customer_profile.cash_on_delivery_allowed = True
        self.user.customer_profile.save(update_fields=['cash_on_delivery_allowed'])

        self.assertTrue(customer_can_use_cash_on_delivery(self.user))
        self.assertIn('cash_on_delivery', self._method_codes(self.user))
        self.assertEqual(get_payment_method('cash_on_delivery', user=self.user)['code'], 'cash_on_delivery')

    def test_staff_can_use_cash_on_delivery_for_admin_operations(self):
        self.assertTrue(customer_can_use_cash_on_delivery(self.staff))
        self.assertIn('cash_on_delivery', self._method_codes(self.staff))

    def test_customer_approval_can_be_disabled_by_admin_setting(self):
        PaymentProviderConfiguration.objects.filter(provider='cash_on_delivery').update(
            public_config={'requires_customer_approval': False, 'prompt_before_dispatch': True}
        )

        self.assertTrue(customer_can_use_cash_on_delivery(self.user))
        self.assertIn('cash_on_delivery', self._method_codes(self.user))


class PesapalStatusHandlingTests(TestCase):
    def _payment(self, **overrides):
        defaults = {
            'method': 'pesapal',
            'provider': 'pesapal',
            'reference': 'PAY-ABC123',
            'amount': Decimal('1250.00'),
            'currency': 'KES',
            'external_reference': 'TRACK-123',
            'status': PaymentSession.STATUS_PENDING,
        }
        defaults.update(overrides)
        return PaymentSession.objects.create(**defaults)

    def test_status_code_marks_payment_paid(self):
        payment = self._payment()

        handle_transaction_status(
            payment,
            {
                'status_code': 1,
                'payment_status_description': 'Completed',
                'merchant_reference': payment.reference,
                'amount': '1250.00',
                'currency': 'KES',
                'confirmation_code': 'CONFIRM-1',
            },
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentSession.STATUS_PAID)
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(payment.metadata['pesapal_status_code'], '1')
        self.assertEqual(payment.metadata['pesapal_confirmation_code'], 'CONFIRM-1')
        self.assertTrue(PaymentEvent.objects.filter(payment_session=payment, kind=PaymentEvent.KIND_STATUS_APPLIED).exists())

    def test_duplicate_success_status_is_ignored_after_paid(self):
        payment = self._payment(status=PaymentSession.STATUS_PAID)

        handle_transaction_status(
            payment,
            {
                'status_code': 1,
                'payment_status_description': 'Completed',
                'merchant_reference': payment.reference,
                'amount': '1250.00',
                'currency': 'KES',
                'confirmation_code': 'CONFIRM-1',
            },
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentSession.STATUS_PAID)
        self.assertTrue(PaymentEvent.objects.filter(payment_session=payment, kind=PaymentEvent.KIND_STATUS_IGNORED).exists())

    def test_status_payload_amount_mismatch_is_rejected(self):
        payment = self._payment()

        with self.assertRaises(PesapalGatewayError):
            handle_transaction_status(
                payment,
                {
                    'status_code': 1,
                    'merchant_reference': payment.reference,
                    'amount': '999.00',
                    'currency': 'KES',
                },
            )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentSession.STATUS_PENDING)

    def test_status_payload_reference_mismatch_is_rejected(self):
        payment = self._payment()

        with self.assertRaises(PesapalGatewayError):
            handle_transaction_status(
                payment,
                {
                    'status_code': 1,
                    'merchant_reference': 'OTHER-REFERENCE',
                    'amount': '1250.00',
                    'currency': 'KES',
                },
            )

    @patch('apps.payments.pesapal._request_access_token', return_value='TOKEN')
    @patch('apps.payments.pesapal._post_json', return_value={'status': '200', 'message': 'Refund request successfully'})
    def test_refund_request_uses_confirmation_code(self, post_json, request_access_token):
        payment = self._payment(
            status=PaymentSession.STATUS_PAID,
            metadata={'pesapal_confirmation_code': 'CONFIRM-1'},
        )

        response = request_refund(payment, amount=Decimal('100.00'), username='Admin User', remarks='Returned item')

        self.assertEqual(response['status'], '200')
        post_json.assert_called_once_with(
            '/Transactions/RefundRequest',
            {
                'confirmation_code': 'CONFIRM-1',
                'amount': '100.00',
                'username': 'Admin User',
                'remarks': 'Returned item',
            },
            token='TOKEN',
        )

    def test_refund_request_requires_confirmation_code(self):
        payment = self._payment(status=PaymentSession.STATUS_PAID)

        with self.assertRaises(PesapalGatewayError):
            request_refund(payment, amount=Decimal('100.00'), username='Admin User', remarks='Returned item')


class PaymentReconciliationTests(TestCase):
    def _payment(self, **overrides):
        defaults = {
            'method': 'pesapal',
            'provider': 'pesapal',
            'reference': 'PAY-ABC123',
            'amount': Decimal('1250.00'),
            'currency': 'KES',
            'external_reference': 'TRACK-123',
            'status': PaymentSession.STATUS_PENDING,
        }
        defaults.update(overrides)
        return PaymentSession.objects.create(**defaults)

    def test_paid_payment_without_order_needs_attention(self):
        payment = self._payment(status=PaymentSession.STATUS_PAID)

        reconciliation = payment_reconciliation(payment)

        self.assertEqual(reconciliation['status'], 'paid_no_order')
        self.assertTrue(reconciliation['needs_attention'])
        self.assertEqual(reconciliation['severity'], 'critical')

    def test_old_pending_payment_is_flagged(self):
        payment = self._payment()
        PaymentSession.objects.filter(pk=payment.pk).update(created_at=timezone.now() - timedelta(minutes=31))
        payment.refresh_from_db()

        reconciliation = payment_reconciliation(payment)

        self.assertEqual(reconciliation['status'], 'pending_too_long')
        self.assertFalse(reconciliation['needs_attention'])
        self.assertEqual(reconciliation['severity'], 'warning')

    def test_sync_payment_reconciliation_creates_pending_ledger_row(self):
        payment = self._payment(external_reference='')

        ledger = sync_payment_reconciliation(payment)

        self.assertEqual(ledger.status, PaymentReconciliation.STATUS_PENDING)
        self.assertEqual(ledger.payment_session, payment)
        self.assertEqual(ledger.merchant_reference, payment.reference)
        self.assertEqual(ledger.expected_amount, payment.amount)
        self.assertEqual(ledger.paid_amount, Decimal('0.00'))

    def test_sync_payment_reconciliation_flags_paid_without_order_for_review(self):
        payment = self._payment(status=PaymentSession.STATUS_PAID)

        ledger = sync_payment_reconciliation(payment)

        self.assertEqual(ledger.status, PaymentReconciliation.STATUS_MANUAL_REVIEW)
        self.assertIn('Payment is confirmed but no order is linked.', ledger.issues)
        self.assertEqual(ledger.paid_amount, payment.amount)


class PesapalNotificationSerializerTests(TestCase):
    def test_accepts_snake_case_post_payload(self):
        request = APIRequestFactory().post('/ipn/', data={}, format='json')
        serializer = PesapalNotificationSerializer(
            data={
                'order_tracking_id': 'TRACK-123',
                'order_merchant_reference': 'PAY-ABC123',
                'order_notification_type': 'IPNCHANGE',
            },
            context={'request': request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['order_tracking_id'], 'TRACK-123')
        self.assertEqual(serializer.validated_data['merchant_reference'], 'PAY-ABC123')
        self.assertEqual(serializer.validated_data['notification_type'], 'IPNCHANGE')

    def test_accepts_camel_case_query_payload(self):
        request = APIRequestFactory().get(
            '/ipn/?orderTrackingId=TRACK-123&orderMerchantReference=PAY-ABC123&orderNotificationType=IPNCHANGE'
        )
        serializer = PesapalNotificationSerializer(data={}, context={'request': request})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['order_tracking_id'], 'TRACK-123')
        self.assertEqual(serializer.validated_data['merchant_reference'], 'PAY-ABC123')
        self.assertEqual(serializer.validated_data['notification_type'], 'IPNCHANGE')
