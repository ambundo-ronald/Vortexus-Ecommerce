from django.core.management.base import BaseCommand

from apps.image_search.tasks import backfill_product_image_embeddings
from apps.search.tasks import reindex_all_products


class Command(BaseCommand):
    help = 'Reindex product search documents and image embeddings into OpenSearch.'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=500)
        parser.add_argument('--limit', type=int, default=None)

    def handle(self, *args, **options):
        batch_size = max(options['batch_size'], 1)
        limit = options['limit']

        indexed_products = reindex_all_products.run(batch_size=batch_size)
        indexed_embeddings = backfill_product_image_embeddings.run(limit=limit)

        self.stdout.write(
            self.style.SUCCESS(
                f'Reindexed {indexed_products} product search documents and {indexed_embeddings} image embedding documents.'
            )
        )
