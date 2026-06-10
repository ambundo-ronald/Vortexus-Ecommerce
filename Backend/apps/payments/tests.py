from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.api.payment_serializers import PesapalNotificationSerializer

from .models import PaymentSession
from .pesapal import PesapalGatewayError, handle_transaction_status
from .services import _payment_method_capabilities


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
