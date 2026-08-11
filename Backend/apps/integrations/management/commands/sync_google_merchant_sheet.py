from django.core.management.base import BaseCommand

from apps.integrations.google_merchant_sheets import sync_google_merchant_sheet


class Command(BaseCommand):
    help = 'Write the Google Merchant product feed into a configured Google Sheet.'

    def add_arguments(self, parser):
        parser.add_argument('--spreadsheet-id', default='', help='Override GOOGLE_MERCHANT_SHEETS_SPREADSHEET_ID.')
        parser.add_argument('--range', dest='range_name', default='', help='A1 update range, for example Sheet1!A1:AN.')
        parser.add_argument('--clear-range', default='', help='A1 clear range before writing, for example Sheet1!A:AN.')
        parser.add_argument('--country', default='KE', help='Tax country code used for tax-inclusive feed pricing.')

    def handle(self, *args, **options):
        result = sync_google_merchant_sheet(
            spreadsheet_id=options['spreadsheet_id'],
            range_name=options['range_name'],
            clear_range=options['clear_range'],
            tax_country_code=options['country'],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {result['products_written']} product(s), "
                f"{result['updated_cells']} cell(s), range {result['updated_range'] or result['range']}."
            )
        )
