from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import AccountingBankTransaction, AccountingJournalEntry, AccountingPaymentLedgerEntry
from .services import (
    account,
    cancel_bank_transaction,
    ensure_default_chart_of_accounts,
    post_payment_received,
    post_refund,
    post_sales_order,
    reconcile_bank_transaction,
    record_payment_ledger,
    submit_journal_entry,
    trial_balance,
)


class AccountingLedgerTests(TestCase):
    def test_default_chart_and_balanced_journal(self):
        ensure_default_chart_of_accounts()

        entry = submit_journal_entry(
            reference='JE-TEST-1',
            entry_type=AccountingJournalEntry.TYPE_MANUAL,
            lines=[
                {'account': account('1000'), 'debit': Decimal('100.00'), 'remarks': 'Bank debit'},
                {'account': account('4000'), 'credit': Decimal('100.00'), 'remarks': 'Revenue credit'},
            ],
            memo='Test journal',
        )

        self.assertEqual(entry.status, AccountingJournalEntry.STATUS_SUBMITTED)
        self.assertEqual(entry.total_debit, Decimal('100.00'))
        self.assertEqual(entry.total_credit, Decimal('100.00'))
        self.assertEqual(entry.lines.count(), 2)

        rows = {row['code']: row for row in trial_balance()}
        self.assertEqual(rows['1000']['debit'], Decimal('100.00'))
        self.assertEqual(rows['4000']['credit'], Decimal('100.00'))

    def test_unbalanced_journal_is_rejected(self):
        ensure_default_chart_of_accounts()

        with self.assertRaises(ValueError):
            submit_journal_entry(
                reference='JE-BAD-1',
                entry_type=AccountingJournalEntry.TYPE_MANUAL,
                lines=[
                    {'account': account('1000'), 'debit': Decimal('100.00')},
                    {'account': account('4000'), 'credit': Decimal('99.00')},
                ],
            )

    def test_payment_ledger_uses_against_voucher_for_outstanding_tracking(self):
        ensure_default_chart_of_accounts()

        record_payment_ledger(
            account_type=AccountingPaymentLedgerEntry.TYPE_RECEIVABLE,
            account_obj=account('1100'),
            party_type='customer',
            party_id='1',
            voucher_type='Sales Order',
            voucher_no='100001',
            against_voucher_type='Sales Order',
            against_voucher_no='100001',
            amount=Decimal('100.00'),
        )
        record_payment_ledger(
            account_type=AccountingPaymentLedgerEntry.TYPE_RECEIVABLE,
            account_obj=account('1100'),
            party_type='customer',
            party_id='1',
            voucher_type='Payment Entry',
            voucher_no='PAY-1',
            against_voucher_type='Sales Order',
            against_voucher_no='100001',
            amount=Decimal('-80.00'),
        )

        outstanding = sum(row.amount for row in AccountingPaymentLedgerEntry.objects.filter(against_voucher_no='100001'))
        self.assertEqual(outstanding, Decimal('20.00'))

    def test_full_refund_does_not_reopen_customer_receivable(self):
        Order = apps.get_model('order', 'Order')
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
        order = Order.objects.create(
            number='100900',
            currency='KES',
            total_incl_tax=Decimal('1000.00'),
            total_excl_tax=Decimal('1000.00'),
            status='Delivered',
            date_placed=timezone.now(),
        )
        payment = PaymentSession.objects.create(
            order=order,
            method=PaymentSession.METHOD_CASH_ON_DELIVERY,
            provider='cash_on_delivery',
            reference='PAY-100900',
            amount=Decimal('1000.00'),
            currency='KES',
            status=PaymentSession.STATUS_AUTHORIZED,
        )
        refund = PaymentRefundLedger.objects.create(
            payment_session=payment,
            order=order,
            refund_reference='REFUND-PAY-100900',
            amount=Decimal('1000.00'),
            currency='KES',
            gateway='cash_on_delivery',
            status=PaymentRefundLedger.STATUS_SUCCEEDED,
            completion_state=PaymentRefundLedger.COMPLETION_FULL_COMPLETED,
        )

        post_sales_order(order)
        post_payment_received(payment)
        post_refund(refund)

        outstanding = sum(row.amount for row in AccountingPaymentLedgerEntry.objects.filter(against_voucher_no=order.number))
        rows = trial_balance()
        totals = {
            'debit': sum(row['debit'] for row in rows),
            'credit': sum(row['credit'] for row in rows),
        }
        self.assertEqual(outstanding, Decimal('0.00'))
        self.assertEqual(totals['debit'], Decimal('3000.00'))
        self.assertEqual(totals['credit'], Decimal('3000.00'))

    def test_unlinked_bank_transaction_reconciles_to_suspense(self):
        ensure_default_chart_of_accounts()
        transaction = AccountingBankTransaction.objects.create(
            transaction_date=timezone.localdate(),
            reference_number='BANK-001',
            deposit=Decimal('500.00'),
            currency='KES',
            description='Unmatched customer payment',
        )

        allocation = reconcile_bank_transaction(
            bank_transaction=transaction,
            allocated_amount=Decimal('500.00'),
            note='Hold in suspense until order is found.',
        )

        transaction.refresh_from_db()
        self.assertEqual(transaction.status, AccountingBankTransaction.STATUS_RECONCILED)
        self.assertEqual(allocation.allocated_amount, Decimal('500.00'))
        self.assertEqual(allocation.journal_entry.reference, f'BANK-RECON-{transaction.id}')
        self.assertEqual(allocation.journal_entry.lines.count(), 2)
        suspense_line = allocation.journal_entry.lines.get(account__code='9999')
        self.assertEqual(suspense_line.credit, Decimal('500.00'))

    def test_reconciled_bank_transaction_cannot_be_cancelled(self):
        ensure_default_chart_of_accounts()
        transaction = AccountingBankTransaction.objects.create(
            transaction_date=timezone.localdate(),
            reference_number='BANK-002',
            deposit=Decimal('250.00'),
            currency='KES',
        )
        reconcile_bank_transaction(bank_transaction=transaction, allocated_amount=Decimal('250.00'))

        with self.assertRaises(ValueError):
            cancel_bank_transaction(bank_transaction=transaction, note='Wrongly cancelled')

    def test_admin_can_import_bank_transactions_from_csv(self):
        user = get_user_model().objects.create_superuser(
            username='csv-admin',
            email='admin@example.com',
            password='pass',
        )
        client = APIClient()
        client.force_authenticate(user=user)
        csv_file = SimpleUploadedFile(
            'statement.csv',
            (
                'Date,Reference,Description,Deposit\n'
                '2026-07-30,MPESA123,Customer payment,1000.00\n'
                '2026-07-30,MPESA124,Second payment,500.00\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = client.post(
            '/api/v1/admin/accounting/bank-transactions/import/',
            {'file': csv_file, 'provider': 'mpesa', 'currency': 'KES'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['summary']['created'], 2)
        self.assertEqual(AccountingBankTransaction.objects.filter(provider='mpesa').count(), 2)

    def test_csv_import_skips_duplicate_reference(self):
        user = get_user_model().objects.create_superuser(
            username='csv-admin-2',
            email='admin2@example.com',
            password='pass',
        )
        AccountingBankTransaction.objects.create(
            transaction_date=timezone.localdate(),
            provider='mpesa',
            reference_number='MPESA-DUP',
            transaction_id='MPESA-DUP',
            deposit=Decimal('100.00'),
            currency='KES',
        )
        client = APIClient()
        client.force_authenticate(user=user)
        csv_file = SimpleUploadedFile(
            'statement.csv',
            'Date,Reference,Description,Deposit\n2026-07-30,MPESA-DUP,Duplicate,100.00\n'.encode('utf-8'),
            content_type='text/csv',
        )

        response = client.post(
            '/api/v1/admin/accounting/bank-transactions/import/',
            {'file': csv_file, 'provider': 'mpesa', 'currency': 'KES'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['summary']['created'], 0)
        self.assertEqual(response.data['summary']['skipped'], 1)
