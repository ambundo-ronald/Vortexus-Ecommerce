from django.core.management.base import BaseCommand

from apps.image_search.tasks import backfill_product_image_embeddings


class Command(BaseCommand):
    help = 'Backfill image embeddings into OpenSearch for product images.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously in this process instead of queuing Celery tasks.',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        run_sync = options['sync']

        if run_sync:
            count = backfill_product_image_embeddings.run(limit=limit)
            self.stdout.write(self.style.SUCCESS(f'Indexed embeddings for {count} products'))
            return

        if limit:
            task = backfill_product_image_embeddings.delay(limit=limit)
        else:
            task = backfill_product_image_embeddings.delay()
        self.stdout.write(f'Queued backfill task: {task.id}')
