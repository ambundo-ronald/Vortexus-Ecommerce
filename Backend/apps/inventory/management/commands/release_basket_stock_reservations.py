from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Release stock allocations created by basket reservations and delete the reservation rows.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report affected reservations without saving changes.')

    def handle(self, *args, **options):
        dry_run = bool(options['dry_run'])
        StockReservation = apps.get_model('inventory', 'StockReservation')
        StockRecord = apps.get_model('partner', 'StockRecord')

        reservations = list(
            StockReservation.objects.select_related('stockrecord', 'line', 'basket')
            .order_by('stockrecord_id', 'id')
        )
        stockrecord_ids = sorted({reservation.stockrecord_id for reservation in reservations})
        released_quantity = 0
        deleted_count = 0

        with transaction.atomic():
            locked_stockrecords = {
                stockrecord.id: stockrecord
                for stockrecord in StockRecord.objects.select_for_update().filter(id__in=stockrecord_ids)
            }

            for reservation in reservations:
                stockrecord = locked_stockrecords.get(reservation.stockrecord_id)
                quantity = int(reservation.quantity or 0)
                if stockrecord and reservation.allocation_applied and quantity:
                    released_quantity += quantity
                    if not dry_run:
                        stockrecord.cancel_allocation(quantity)
                deleted_count += 1

            if not dry_run and reservations:
                StockReservation.objects.filter(id__in=[reservation.id for reservation in reservations]).delete()

            if dry_run:
                transaction.set_rollback(True)

        action = 'Would release' if dry_run else 'Released'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} {released_quantity} allocated unit(s) from {deleted_count} basket reservation(s).'
            )
        )
