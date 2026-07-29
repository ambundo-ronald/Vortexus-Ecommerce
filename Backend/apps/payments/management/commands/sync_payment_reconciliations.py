from django.core.management.base import BaseCommand

from apps.payments.services import sync_payment_reconciliation


class Command(BaseCommand):
    help = 'Create or refresh payment reconciliation rows for existing payment sessions.'

    def add_arguments(self, parser):
        parser.add_argument('--reference', default='', help='Sync one payment session by merchant reference.')
        parser.add_argument('--status', default='', help='Filter payment sessions by status.')
        parser.add_argument('--limit', type=int, default=0, help='Maximum number of payment sessions to process.')

    def handle(self, *args, **options):
        PaymentSession = self._payment_session_model()
        queryset = PaymentSession.objects.select_related('order').order_by('id')
        reference = (options.get('reference') or '').strip()
        status = (options.get('status') or '').strip()
        limit = int(options.get('limit') or 0)

        if reference:
            queryset = queryset.filter(reference=reference)
        if status:
            queryset = queryset.filter(status=status)
        if limit > 0:
            queryset = queryset[:limit]

        processed = 0
        for payment_session in queryset.iterator():
            sync_payment_reconciliation(payment_session)
            processed += 1

        self.stdout.write(self.style.SUCCESS(f'Synced {processed} payment reconciliation row(s).'))

    @staticmethod
    def _payment_session_model():
        from django.apps import apps

        return apps.get_model('payments', 'PaymentSession')
