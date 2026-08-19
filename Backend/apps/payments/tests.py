from decimal import Decimal
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from apps.api.payment_serializers import PesapalNotificationSerializer
from apps.api.payment_config_views import _refund_request_summary
from apps.accounts.models import CustomerProfile

from .models import PaymentEvent, PaymentProviderConfiguration, PaymentReconciliation, PaymentRefundLedger, PaymentReturnCase, PaymentSession
from .mpesa import initiate_stk_push, query_stk_push_status
from .pesapal import PesapalGatewayError, handle_transaction_status, request_refund
from .services import (
    _payment_method_capabilities,
    available_payment_methods,
    bank_transfer_state,
    cash_on_delivery_state,
    customer_can_use_bank_transfer,
    customer_can_use_cash_on_delivery,
    get_payment_method,
    initialize_payment_session,
    payment_requires_prepayment,
    payment_reconciliation,
    record_payment_refund_ledger,
    create_payment_return_case,
    sync_payment_reconciliation,
    update_payment_refund_ledger_status,
    update_payment_return_case,
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


class MpesaBuyGoodsRequestTests(SimpleTestCase):
    def _payment(self):
        return SimpleNamespace(
            amount=Decimal('8.70'),
            payer_phone='0712345678',
            reference='PAY-LIVE-1',
            provider_payload={},
            STATUS_PENDING='pending',
            status='initialized',
            save=Mock(),
        )

    @staticmethod
    def _setting(provider, key, default=''):
        values = {
            'base_url': 'https://api.safaricom.co.ke',
            'consumer_key': 'live-key',
            'consumer_secret': 'live-secret',
            'shortcode': '4342093',
            'till_number': '1550097',
            'passkey': 'live-passkey',
            'callback_url': 'https://api.example.com/api/v1/payments/mpesa/callback/',
            'transaction_type': 'CustomerBuyGoodsOnline',
        }
        return values.get(key, default)

    @patch('apps.payments.mpesa._timestamp', return_value='20260819122446')
    @patch('apps.payments.mpesa._generate_access_token', return_value='TOKEN')
    @patch('apps.payments.mpesa._post_json', return_value={
        'MerchantRequestID': 'merchant-1',
        'CheckoutRequestID': 'checkout-1',
        'ResponseCode': '0',
    })
    @patch('apps.payments.mpesa.get_payment_setting')
    @patch('apps.payments.mpesa.provider_is_enabled', return_value=True)
    def test_buy_goods_uses_api_shortcode_and_separate_till_number(
        self,
        _provider_enabled,
        get_setting,
        post_json,
        _access_token,
        _timestamp,
    ):
        get_setting.side_effect = self._setting

        initiate_stk_push(self._payment())

        payload = post_json.call_args.kwargs['payload']
        self.assertEqual(payload['BusinessShortCode'], '4342093')
        self.assertEqual(payload['PartyB'], '1550097')
        self.assertEqual(payload['TransactionType'], 'CustomerBuyGoodsOnline')

    @patch('apps.payments.mpesa._timestamp', return_value='20260819122446')
    @patch('apps.payments.mpesa._generate_access_token', return_value='TOKEN')
    @patch('apps.payments.mpesa._post_json', return_value={'ResultCode': '0'})
    @patch('apps.payments.mpesa.get_payment_setting')
    @patch('apps.payments.mpesa.provider_is_enabled', return_value=True)
    def test_status_query_uses_api_shortcode_not_till_number(
        self,
        _provider_enabled,
        get_setting,
        post_json,
        _access_token,
        _timestamp,
    ):
        get_setting.side_effect = self._setting
        payment = self._payment()
        payment.provider_payload = {'checkout_request_id': 'checkout-1'}

        query_stk_push_status(payment)

        payload = post_json.call_args.kwargs['payload']
        self.assertEqual(payload['BusinessShortCode'], '4342093')
        self.assertNotIn('PartyB', payload)


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
        self.assertFalse(cash_on_delivery_state(self.user)['available'])
        self.assertNotIn('cash_on_delivery', self._method_codes(self.user))

        self.user.customer_profile.cash_on_delivery_allowed = True
        self.user.customer_profile.save(update_fields=['cash_on_delivery_allowed'])

        self.assertTrue(customer_can_use_cash_on_delivery(self.user))
        self.assertTrue(cash_on_delivery_state(self.user)['available'])
        self.assertIn('cash_on_delivery', self._method_codes(self.user))
        self.assertEqual(get_payment_method('cash_on_delivery', user=self.user)['code'], 'cash_on_delivery')
        self.assertFalse(payment_requires_prepayment('cash_on_delivery', user=self.user))

    def test_cash_on_delivery_state_respects_provider_enabled_flag(self):
        self.user.customer_profile.cash_on_delivery_allowed = True
        self.user.customer_profile.save(update_fields=['cash_on_delivery_allowed'])
        PaymentProviderConfiguration.objects.filter(provider='cash_on_delivery').update(is_enabled=False)

        state = cash_on_delivery_state(self.user)

        self.assertTrue(state['customer_approved'])
        self.assertFalse(state['provider_available'])
        self.assertFalse(state['available'])
        self.assertNotIn('cash_on_delivery', self._method_codes(self.user))

    def test_staff_can_use_cash_on_delivery_for_admin_operations(self):
        self.assertTrue(customer_can_use_cash_on_delivery(self.staff))
        self.assertIn('cash_on_delivery', self._method_codes(self.staff))

    def test_customer_approval_can_be_disabled_by_admin_setting(self):
        PaymentProviderConfiguration.objects.filter(provider='cash_on_delivery').update(
            public_config={'requires_customer_approval': False, 'prompt_before_dispatch': True}
        )

        self.assertTrue(customer_can_use_cash_on_delivery(self.user))
        self.assertIn('cash_on_delivery', self._method_codes(self.user))

    def test_approved_customer_can_initialize_cash_on_delivery_session(self):
        self.user.customer_profile.cash_on_delivery_allowed = True
        self.user.customer_profile.save(update_fields=['cash_on_delivery_allowed'])

        payment = initialize_payment_session(
            basket=None,
            user=self.user,
            method_code='cash_on_delivery',
            amount=Decimal('1250.00'),
            currency='KES',
            payer_email=self.user.email,
        )

        self.assertEqual(payment.method, 'cash_on_delivery')
        self.assertEqual(payment.provider, 'cash_on_delivery')
        self.assertEqual(payment.status, PaymentSession.STATUS_AUTHORIZED)


class BankTransferAvailabilityTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='bank-customer', email='bank@example.com', password='password')
        self.staff = self.User.objects.create_user(username='bank-staff', email='bank-staff@example.com', password='password', is_staff=True)
        CustomerProfile.objects.create(user=self.user)
        PaymentProviderConfiguration.objects.create(
            provider='bank_transfer',
            is_enabled=True,
            public_config={'requires_customer_approval': True},
        )

    def _method_codes(self, user=None):
        return {method['code'] for method in available_payment_methods(user=user)}

    def test_bank_transfer_is_not_enabled_without_provider_config(self):
        PaymentProviderConfiguration.objects.filter(provider='bank_transfer').delete()

        self.user.customer_profile.bank_transfer_allowed = True
        self.user.customer_profile.save(update_fields=['bank_transfer_allowed'])

        self.assertNotIn('bank_transfer', self._method_codes(self.user))

    def test_bank_transfer_requires_customer_approval(self):
        self.assertFalse(customer_can_use_bank_transfer(self.user))
        self.assertFalse(bank_transfer_state(self.user)['available'])
        self.assertNotIn('bank_transfer', self._method_codes(self.user))

        self.user.customer_profile.bank_transfer_allowed = True
        self.user.customer_profile.save(update_fields=['bank_transfer_allowed'])

        self.assertTrue(customer_can_use_bank_transfer(self.user))
        self.assertTrue(bank_transfer_state(self.user)['available'])
        self.assertIn('bank_transfer', self._method_codes(self.user))
        self.assertEqual(get_payment_method('bank_transfer', user=self.user)['code'], 'bank_transfer')
        self.assertFalse(payment_requires_prepayment('bank_transfer', user=self.user))

    def test_staff_can_use_bank_transfer_for_admin_operations(self):
        self.assertTrue(customer_can_use_bank_transfer(self.staff))
        self.assertIn('bank_transfer', self._method_codes(self.staff))

    def test_approved_customer_can_initialize_bank_transfer_session(self):
        self.user.customer_profile.bank_transfer_allowed = True
        self.user.customer_profile.save(update_fields=['bank_transfer_allowed'])

        payment = initialize_payment_session(
            basket=None,
            user=self.user,
            method_code='bank_transfer',
            amount=Decimal('1250.00'),
            currency='KES',
            payer_email=self.user.email,
        )

        self.assertEqual(payment.method, 'bank_transfer')
        self.assertEqual(payment.provider, 'bank_transfer')
        self.assertEqual(payment.status, PaymentSession.STATUS_AUTHORIZED)


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

    def test_refund_summary_handles_select_related_payment_queryset(self):
        self._payment(
            status=PaymentSession.STATUS_PAID,
            metadata={'refund_requests': [{'amount': '250.00', 'status': PaymentRefundLedger.STATUS_SUBMITTED}]},
        )

        summary = _refund_request_summary(PaymentSession.objects.select_related('order').all())

        self.assertEqual(summary, {'count': 1, 'total': 250.0})

    def test_finance_summary_excludes_unlinked_cancelled_and_refunded_collections(self):
        User = get_user_model()
        admin = User.objects.create_superuser(
            username='finance-admin',
            email='finance-admin@example.com',
            password='password',
        )
        Order = apps.get_model('order', 'Order')
        order = Order.objects.create(
            number='100500',
            currency='KES',
            total_incl_tax=Decimal('25000.00'),
            total_excl_tax=Decimal('25000.00'),
            status='Placed',
            date_placed=timezone.now(),
        )
        collectible = self._payment(
            reference='PAY-COLLECTIBLE',
            status=PaymentSession.STATUS_AUTHORIZED,
            amount=Decimal('25000.00'),
            order=order,
        )
        self._payment(
            reference='PAY-NO-ORDER',
            status=PaymentSession.STATUS_AUTHORIZED,
            amount=Decimal('51000.00'),
        )
        cancelled = self._payment(
            reference='PAY-CANCELLED',
            status=PaymentSession.STATUS_AUTHORIZED,
            amount=Decimal('8000.00'),
            order=order,
        )
        PaymentReconciliation.objects.create(
            payment_session=cancelled,
            order=order,
            provider=cancelled.provider,
            method=cancelled.method,
            merchant_reference=cancelled.reference,
            expected_amount=cancelled.amount,
            paid_amount=cancelled.amount,
            currency=cancelled.currency,
            status=PaymentReconciliation.STATUS_CANCELLED,
        )
        PaymentRefundLedger.objects.create(
            payment_session=collectible,
            order=order,
            refund_reference='REFUND-COLLECTIBLE',
            amount=Decimal('25000.00'),
            currency='KES',
            gateway='bank_transfer',
            status=PaymentRefundLedger.STATUS_SUCCEEDED,
            completion_state=PaymentRefundLedger.COMPLETION_FULL_COMPLETED,
        )
        client = APIClient()
        client.force_authenticate(admin)

        response = client.get('/api/v1/admin/finance/summary/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['collections']['gross_total'], 25000.0)
        self.assertEqual(response.data['collections']['total'], 0.0)
        self.assertEqual(response.data['collections']['excluded_count'], 2)
        self.assertEqual(response.data['refunds'], {'count': 1, 'total': 25000.0})


class AdminPaymentCancellationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def _payment(self, **overrides):
        defaults = {
            'method': 'bank_transfer',
            'provider': 'bank_transfer',
            'reference': 'PAY-BANK123',
            'amount': Decimal('2500.00'),
            'currency': 'KES',
            'status': PaymentSession.STATUS_AUTHORIZED,
        }
        defaults.update(overrides)
        return PaymentSession.objects.create(**defaults)

    def test_platform_admin_can_cancel_unlinked_payment(self):
        payment = self._payment()

        response = self.client.post(
            f'/api/v1/admin/payments/{payment.reference}/cancel/',
            {'reason': 'Manual bank payment was not received.'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentSession.STATUS_CANCELLED)
        self.assertTrue(payment.metadata['admin_cancelled'])
        self.assertEqual(payment.metadata['previous_status'], PaymentSession.STATUS_AUTHORIZED)
        self.assertTrue(
            PaymentEvent.objects.filter(
                payment_session=payment,
                kind=PaymentEvent.KIND_STATUS_APPLIED,
                status_after=PaymentSession.STATUS_CANCELLED,
            ).exists()
        )

    def test_linked_payment_must_use_order_refund_or_cancel_workflow(self):
        Order = apps.get_model('order', 'Order')
        order = Order.objects.create(
            number='100001',
            currency='KES',
            total_incl_tax=Decimal('2500.00'),
            total_excl_tax=Decimal('2500.00'),
            status='Placed',
            date_placed=timezone.now(),
        )
        payment = self._payment(order=order)

        response = self.client.post(
            f'/api/v1/admin/payments/{payment.reference}/cancel/',
            {'reason': 'Should not be allowed.'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentSession.STATUS_AUTHORIZED)


class RefundAndReturnWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='refund-admin',
            email='refund-admin@example.com',
            password='password',
        )

    def _payment(self, **overrides):
        defaults = {
            'method': PaymentSession.METHOD_BANK_TRANSFER,
            'provider': 'bank_transfer',
            'reference': 'PAY-REFUND123',
            'amount': Decimal('1000.00'),
            'currency': 'KES',
            'status': PaymentSession.STATUS_AUTHORIZED,
        }
        defaults.update(overrides)
        return PaymentSession.objects.create(**defaults)

    def _order_line_with_stock(self, *, quantity=2, stock=5, line_total=Decimal('1000.00')):
        ProductClass = apps.get_model('catalogue', 'ProductClass')
        Product = apps.get_model('catalogue', 'Product')
        Partner = apps.get_model('partner', 'Partner')
        StockRecord = apps.get_model('partner', 'StockRecord')
        Order = apps.get_model('order', 'Order')
        Line = apps.get_model('order', 'Line')

        product_class, _ = ProductClass.objects.get_or_create(name='Return test products')
        product = Product.objects.create(
            product_class=product_class,
            structure=Product.STANDALONE,
            upc='RETURN-SKU',
            title='Return test product',
            slug='return-test-product',
            is_public=True,
        )
        partner = Partner.objects.create(name='Return Test Partner')
        stockrecord = StockRecord.objects.create(
            product=product,
            partner=partner,
            partner_sku='RETURN-SKU',
            price_currency='KES',
            price=(line_total / Decimal(str(quantity))).quantize(Decimal('0.01')),
            num_in_stock=stock,
        )
        order = Order.objects.create(
            number='100903',
            currency='KES',
            total_incl_tax=line_total,
            total_excl_tax=line_total,
            status='Delivered',
            date_placed=timezone.now(),
        )
        line = Line.objects.create(
            order=order,
            partner=partner,
            partner_name=partner.name,
            partner_sku=stockrecord.partner_sku,
            stockrecord=stockrecord,
            product=product,
            title=product.title,
            upc=product.upc,
            quantity=quantity,
            line_price_incl_tax=line_total,
            line_price_excl_tax=line_total,
            line_price_before_discounts_incl_tax=line_total,
            line_price_before_discounts_excl_tax=line_total,
            unit_price_incl_tax=(line_total / Decimal(str(quantity))).quantize(Decimal('0.01')),
            unit_price_excl_tax=(line_total / Decimal(str(quantity))).quantize(Decimal('0.01')),
            num_allocated=quantity,
            allocation_cancelled=0,
        )
        return order, line, stockrecord

    def test_refund_can_be_submitted_and_completed_with_accounting_entry(self):
        payment = self._payment()
        refund = record_payment_refund_ledger(
            payment,
            amount=Decimal('400.00'),
            reason='Customer refund',
            refund_reference='REFUND-TEST-001',
            requested_by=self.admin,
        )

        refund = update_payment_refund_ledger_status(
            refund,
            action='submit',
            provider_reference='BANK-REF-1',
            reviewed_by=self.admin,
        )
        self.assertEqual(refund.status, PaymentRefundLedger.STATUS_SUBMITTED)
        self.assertEqual(refund.provider_reference, 'BANK-REF-1')

        refund = update_payment_refund_ledger_status(
            refund,
            action='succeed',
            provider_reference='BANK-REF-2',
            reviewed_by=self.admin,
        )
        self.assertEqual(refund.status, PaymentRefundLedger.STATUS_SUCCEEDED)
        self.assertEqual(refund.completion_state, PaymentRefundLedger.COMPLETION_PARTIAL_COMPLETED)
        self.assertIsNotNone(refund.processed_at)

        AccountingJournalEntry = apps.get_model('accounting', 'AccountingJournalEntry')
        self.assertTrue(AccountingJournalEntry.objects.filter(reference='REFUND-REFUND-TEST-001').exists())

    def test_refund_completion_requires_submit_first(self):
        payment = self._payment(reference='PAY-REFUND456')
        refund = record_payment_refund_ledger(
            payment,
            amount=Decimal('200.00'),
            reason='Customer refund',
            refund_reference='REFUND-TEST-002',
            requested_by=self.admin,
        )

        with self.assertRaises(ValueError):
            update_payment_refund_ledger_status(refund, action='succeed', reviewed_by=self.admin)

    def test_full_refund_marks_order_refunded(self):
        Order = apps.get_model('order', 'Order')
        OrderStatusChange = apps.get_model('order', 'OrderStatusChange')
        order = Order.objects.create(
            number='100902',
            currency='KES',
            total_incl_tax=Decimal('1000.00'),
            total_excl_tax=Decimal('1000.00'),
            status='Delivered',
            date_placed=timezone.now(),
        )
        payment = self._payment(reference='PAY-FULL-REFUND', order=order, amount=Decimal('1000.00'))
        refund = record_payment_refund_ledger(
            payment,
            amount=Decimal('1000.00'),
            reason='Full refund',
            refund_reference='REFUND-FULL-001',
            status=PaymentRefundLedger.STATUS_SUBMITTED,
            requested_by=self.admin,
        )

        update_payment_refund_ledger_status(refund, action='succeed', reviewed_by=self.admin)

        order.refresh_from_db()
        self.assertEqual(order.status, 'Refunded')
        self.assertTrue(
            OrderStatusChange.objects.filter(
                order=order,
                old_status='Delivered',
                new_status='Refunded',
            ).exists()
        )

    def test_return_workflow_prevents_skipping_to_receive(self):
        return_case = PaymentReturnCase(status=PaymentReturnCase.STATUS_REQUESTED)

        with self.assertRaises(ValueError):
            update_payment_return_case(return_case, action='receive', reviewed_by=self.admin)

    def test_return_accept_restocks_without_creating_refund_ledger(self):
        order, line, stockrecord = self._order_line_with_stock(quantity=2, stock=5, line_total=Decimal('1000.00'))
        payment = self._payment(reference='PAY-RETURN-ACCEPT', order=order, amount=Decimal('1000.00'))
        return_case = create_payment_return_case(
            payment_session=payment,
            line=line,
            quantity=1,
            restock_decision=PaymentReturnCase.RESTOCK_RESTOCK,
            requested_by=self.admin,
        )
        update_payment_return_case(return_case, action='approve', reviewed_by=self.admin)
        update_payment_return_case(return_case, action='receive', reviewed_by=self.admin)

        return_case = update_payment_return_case(
            return_case,
            action='accept',
            accepted_quantity=1,
            restock_decision=PaymentReturnCase.RESTOCK_RESTOCK,
            reviewed_by=self.admin,
        )

        stockrecord.refresh_from_db()
        self.assertEqual(return_case.status, PaymentReturnCase.STATUS_ACCEPTED)
        self.assertEqual(return_case.refund_ledger_id, None)
        self.assertEqual(stockrecord.num_in_stock, 6)
        self.assertIsNotNone(return_case.restocked_at)

    def test_return_creation_blocks_quantity_already_in_return_flow(self):
        order, line, _stockrecord = self._order_line_with_stock(quantity=1, stock=5, line_total=Decimal('1000.00'))
        payment = self._payment(reference='PAY-RETURN-DUPLICATE', order=order, amount=Decimal('1000.00'))
        create_payment_return_case(
            payment_session=payment,
            line=line,
            quantity=1,
            requested_by=self.admin,
        )

        with self.assertRaisesMessage(ValueError, 'This order line already has return/refund quantity in progress or completed.'):
            create_payment_return_case(
                payment_session=payment,
                line=line,
                quantity=1,
                requested_by=self.admin,
            )

    def test_return_refund_creates_refund_reference_after_acceptance(self):
        order, line, _stockrecord = self._order_line_with_stock(quantity=2, stock=5, line_total=Decimal('1000.00'))
        payment = self._payment(reference='PAY-RETURN-REFUND', order=order, amount=Decimal('1000.00'))
        return_case = create_payment_return_case(
            payment_session=payment,
            line=line,
            quantity=1,
            restock_decision=PaymentReturnCase.RESTOCK_RESTOCK,
            requested_by=self.admin,
        )
        update_payment_return_case(return_case, action='approve', reviewed_by=self.admin)
        update_payment_return_case(return_case, action='receive', reviewed_by=self.admin)
        update_payment_return_case(return_case, action='accept', accepted_quantity=1, reviewed_by=self.admin)

        return_case = update_payment_return_case(return_case, action='refund', reviewed_by=self.admin)

        self.assertEqual(return_case.status, PaymentReturnCase.STATUS_REFUNDED)
        self.assertIsNotNone(return_case.refund_ledger_id)
        self.assertEqual(return_case.refund_ledger.refund_reference, f'RETURN-{return_case.return_reference}')
        self.assertEqual(return_case.refund_ledger.status, PaymentRefundLedger.STATUS_SUCCEEDED)


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
