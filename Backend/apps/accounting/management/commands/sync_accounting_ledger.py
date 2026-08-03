from django.apps import apps
from django.core.management.base import BaseCommand

from apps.accounting.services import (
    ensure_default_chart_of_accounts,
    post_payment_received,
    post_refund,
    post_sales_order,
    post_supplier_payable,
    post_supplier_payout,
)


class Command(BaseCommand):
    help = 'Seed chart of accounts and optionally backfill ecommerce accounting ledger entries.'

    def add_arguments(self, parser):
        parser.add_argument('--seed-only', action='store_true', help='Only create default chart of accounts.')
        parser.add_argument('--orders', action='store_true', help='Post sales order accounting entries.')
        parser.add_argument('--payments', action='store_true', help='Post confirmed payment accounting entries.')
        parser.add_argument('--supplier-payables', action='store_true', help='Post supplier payable accounting entries.')
        parser.add_argument('--supplier-payouts', action='store_true', help='Post paid supplier payout accounting entries.')
        parser.add_argument('--refunds', action='store_true', help='Post succeeded refund accounting entries.')

    def handle(self, *args, **options):
        ensure_default_chart_of_accounts()
        self.stdout.write(self.style.SUCCESS('Default chart of accounts is ready.'))
        if options['seed_only']:
            return

        selected = any(options[name] for name in ['orders', 'payments', 'supplier_payables', 'supplier_payouts', 'refunds'])
        run_all = not selected

        if run_all or options['orders']:
            Order = apps.get_model('order', 'Order')
            count = 0
            for order in Order.objects.all().iterator():
                if post_sales_order(order):
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Checked {count} sales order accounting entries.'))

        if run_all or options['payments']:
            PaymentSession = apps.get_model('payments', 'PaymentSession')
            count = 0
            for payment in PaymentSession.objects.filter(status__in=['paid', 'authorized'], order__isnull=False).select_related('order', 'user').iterator():
                if post_payment_received(payment):
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Checked {count} payment accounting entries.'))

        if run_all or options['supplier_payables']:
            SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
            count = 0
            for payable in SupplierPayableLedger.objects.exclude(status='reversed').select_related('supplier', 'partner', 'order').iterator():
                if post_supplier_payable(payable):
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Checked {count} supplier payable accounting entries.'))

        if run_all or options['supplier_payouts']:
            SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
            count = 0
            for batch in SupplierPayoutBatch.objects.filter(status='paid').select_related('supplier', 'partner').iterator():
                if post_supplier_payout(batch):
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Checked {count} supplier payout accounting entries.'))

        if run_all or options['refunds']:
            PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
            count = 0
            for refund in PaymentRefundLedger.objects.filter(status='succeeded').select_related('order', 'payment_session', 'payment_session__user').iterator():
                if post_refund(refund):
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Checked {count} refund accounting entries.'))
