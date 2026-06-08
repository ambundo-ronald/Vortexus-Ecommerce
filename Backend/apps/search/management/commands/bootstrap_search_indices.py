from django.conf import settings
from django.core.management.base import BaseCommand

from apps.common.clients import get_opensearch_client


class Command(BaseCommand):
    help = 'Create OpenSearch indices for product text search and image vector search.'

    product_properties = {
        'id': {'type': 'integer'},
        'title': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
        'sku': {'type': 'keyword'},
        'description': {'type': 'text'},
        'category_slug': {'type': 'keyword'},
        'category_slugs': {'type': 'keyword'},
        'brand': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
        'brand_slug': {'type': 'keyword'},
        'price': {'type': 'float'},
        'currency': {'type': 'keyword'},
        'thumbnail': {'type': 'keyword'},
        'in_stock': {'type': 'boolean'},
        'rating': {'type': 'float'},
        'review_count': {'type': 'integer'},
        'date_updated': {'type': 'date'},
        'attributes_text': {'type': 'text'},
    }
    image_properties = {
        'product_id': {'type': 'integer'},
        'title': {'type': 'text'},
        'sku': {'type': 'keyword'},
        'category_slug': {'type': 'keyword'},
        'category_slugs': {'type': 'keyword'},
        'brand': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
        'brand_slug': {'type': 'keyword'},
        'price': {'type': 'float'},
        'currency': {'type': 'keyword'},
        'thumbnail': {'type': 'keyword'},
        'in_stock': {'type': 'boolean'},
    }

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
                        'properties': self.product_properties
                    },
                },
            )
            self.stdout.write(self.style.SUCCESS(f'Created {product_index} index'))
        else:
            self._put_missing_properties(client, product_index, self.product_properties)
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
                            **self.image_properties,
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
            self._put_missing_properties(client, image_index, self.image_properties)
            self.stdout.write(f'{image_index} index already exists')

    def _put_missing_properties(self, client, index_name, expected_properties):
        mapping = client.indices.get_mapping(index=index_name)
        existing_properties = mapping[index_name].get('mappings', {}).get('properties', {})
        missing = {
            name: definition
            for name, definition in expected_properties.items()
            if name not in existing_properties
        }
        if not missing:
            return
        client.indices.put_mapping(index=index_name, body={'properties': missing})
        fields = ', '.join(sorted(missing))
        self.stdout.write(self.style.SUCCESS(f'Updated {index_name} mapping: {fields}'))
