from django.apps import apps
from django.core.management.base import BaseCommand

from apps.marketplace.payables import sync_supplier_payable_for_allocation, sync_supplier_payables_for_order


class Command(BaseCommand):
    help = 'Create or refresh supplier payable ledger rows from supplier order allocations.'

    def add_arguments(self, parser):
        parser.add_argument('--order-number', dest='order_number', help='Sync payables for one order number.')
        parser.add_argument('--supplier-id', dest='supplier_id', type=int, help='Sync payables for one supplier profile ID.')

    def handle(self, *args, **options):
        Order = apps.get_model('order', 'Order')
        SupplierOrderLineAllocation = apps.get_model('marketplace', 'SupplierOrderLineAllocation')

        order_number = (options.get('order_number') or '').strip()
        supplier_id = options.get('supplier_id')

        if order_number:
            order = Order.objects.get(number=order_number)
            ledgers = sync_supplier_payables_for_order(order)
            self.stdout.write(self.style.SUCCESS(f'Synced {len(ledgers)} supplier payable ledger row(s) for order {order.number}.'))
            return

        allocations = SupplierOrderLineAllocation.objects.select_related(
            'supplier',
            'partner',
            'order',
            'line',
            'product',
            'supplier_offer',
            'stockrecord',
        ).order_by('id')
        if supplier_id:
            allocations = allocations.filter(supplier_id=supplier_id)

        synced = 0
        for allocation in allocations.iterator():
            sync_supplier_payable_for_allocation(allocation)
            synced += 1

        target = f' for supplier {supplier_id}' if supplier_id else ''
        self.stdout.write(self.style.SUCCESS(f'Synced {synced} supplier payable ledger row(s){target}.'))
