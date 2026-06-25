from decimal import Decimal

from django.apps import apps
from django.core.management.base import BaseCommand

from apps.common.currency import convert_amount, default_currency, normalize_currency_code


class Command(BaseCommand):
    help = 'Convert stockrecord prices into a single marketplace currency.'

    def add_arguments(self, parser):
        parser.add_argument('--target-currency', default=default_currency(), help='Currency to store on stockrecords.')
        parser.add_argument('--dry-run', action='store_true', help='Report changes without saving.')

    def handle(self, *args, **options):
        target_currency = normalize_currency_code(options['target_currency']) or default_currency()
        dry_run = bool(options['dry_run'])
        StockRecord = apps.get_model('partner', 'StockRecord')

        updated = 0
        skipped = 0
        queryset = StockRecord.objects.exclude(price_currency=target_currency).select_related('product').order_by('id')
        for stockrecord in queryset.iterator():
            source_currency = normalize_currency_code(stockrecord.price_currency)
            converted, output_currency = convert_amount(stockrecord.price, source_currency, target_currency)
            if normalize_currency_code(output_currency) != target_currency:
                skipped += 1
                self.stderr.write(
                    f'Skipped stockrecord {stockrecord.id}: no conversion rate from {source_currency or "unknown"} to {target_currency}'
                )
                continue

            stockrecord.price = Decimal(str(converted)).quantize(Decimal('0.01'))
            stockrecord.price_currency = target_currency
            updated += 1
            if not dry_run:
                stockrecord.save(update_fields=['price', 'price_currency'])

        action = 'Would update' if dry_run else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} {updated} stockrecords to {target_currency}; skipped {skipped}.'))
