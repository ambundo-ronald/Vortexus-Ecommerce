from django.conf import settings
from django.core.management.base import BaseCommand

from apps.common.clients import get_opensearch_client


class Command(BaseCommand):
    help = 'Create OpenSearch indices for product text search and image vector search.'

    def handle(self, *args, **options):
        client = get_opensearch_client()

        product_index = settings.SEARCH_INDEX_PRODUCTS
        image_index = settings.SEARCH_INDEX_IMAGE_EMBEDDINGS

        if not client.indices.exists(index=product_index):
            client.indices.create(
                index=product_index,
                body={
                    'settings': {'index': {'number_of_shards': 1, 'number_of_replicas': 0}},
                    'mappings': {
                        'properties': {
                            'id': {'type': 'integer'},
                            'title': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
                            'sku': {'type': 'keyword'},
                            'description': {'type': 'text'},
                            'category_slug': {'type': 'keyword'},
                            'price': {'type': 'float'},
                            'currency': {'type': 'keyword'},
                            'thumbnail': {'type': 'keyword'},
                            'in_stock': {'type': 'boolean'},
                            'attributes_text': {'type': 'text'},
                        }
                    },
                },
            )
            self.stdout.write(self.style.SUCCESS(f'Created {product_index} index'))
        else:
            self.stdout.write(f'{product_index} index already exists')

        if not client.indices.exists(index=image_index):
            client.indices.create(
                index=image_index,
                body={
                    'settings': {
                        'index': {
                            'number_of_shards': 1,
                            'number_of_replicas': 0,
                            'knn': True,
                        }
                    },
                    'mappings': {
                        'properties': {
                            'product_id': {'type': 'integer'},
                            'title': {'type': 'text'},
                            'sku': {'type': 'keyword'},
                            'category_slug': {'type': 'keyword'},
                            'price': {'type': 'float'},
                            'currency': {'type': 'keyword'},
                            'thumbnail': {'type': 'keyword'},
                            'in_stock': {'type': 'boolean'},
                            'embedding': {
                                'type': 'knn_vector',
                                'dimension': settings.EMBEDDING_DIMENSION,
                            },
                        }
                    },
                },
            )
            self.stdout.write(self.style.SUCCESS(f'Created {image_index} index'))
        else:
            self.stdout.write(f'{image_index} index already exists')
