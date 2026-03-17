from django.core.management.base import BaseCommand, CommandError
from oscar.core.loading import get_model

from apps.notifications.services import send_order_confirmation_email


class Command(BaseCommand):
    help = 'Send an order confirmation email for an existing order.'

    def add_arguments(self, parser):
        parser.add_argument('order_number')

    def handle(self, *args, **options):
        Order = get_model('order', 'Order')
        try:
            order = Order.objects.select_related('user').get(number=options['order_number'])
        except Order.DoesNotExist as exc:
            raise CommandError(f"Order '{options['order_number']}' does not exist.") from exc

        if send_order_confirmation_email(order):
            self.stdout.write(self.style.SUCCESS(f"Order confirmation email sent for order {order.number}."))
            return

        raise CommandError(f'Order confirmation email was not sent for order {order.number}.')

