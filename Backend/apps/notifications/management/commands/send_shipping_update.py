from django.core.management.base import BaseCommand, CommandError
from oscar.core.loading import get_model

from apps.notifications.services import send_shipping_update_email


class Command(BaseCommand):
    help = 'Send a shipping update email for an existing order.'

    def add_arguments(self, parser):
        parser.add_argument('order_number')
        parser.add_argument('--status-label', required=True)
        parser.add_argument('--tracking-reference', default='')
        parser.add_argument('--note', default='')

    def handle(self, *args, **options):
        Order = get_model('order', 'Order')
        try:
            order = Order.objects.select_related('user').get(number=options['order_number'])
        except Order.DoesNotExist as exc:
            raise CommandError(f"Order '{options['order_number']}' does not exist.") from exc

        if send_shipping_update_email(
            order,
            status_label=options['status_label'],
            tracking_reference=options['tracking_reference'],
            note=options['note'],
        ):
            self.stdout.write(self.style.SUCCESS(f"Shipping update email sent for order {order.number}."))
            return

        raise CommandError(f'Shipping update email was not sent for order {order.number}.')

