from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from opensearchpy.exceptions import OpenSearchException

from apps.common.clients import get_opensearch_client
from apps.common.products import serialize_product_card


class ProductSearchService:
    def search(self, query: str, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        if query.strip():
            try:
                return self._search_opensearch(query=query, filters=filters, page=page, page_size=page_size)
            except (OpenSearchException, ValueError, KeyError):
                pass

        return self._search_database(query=query, filters=filters, page=page, page_size=page_size)

    def _search_opensearch(self, query: str, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        client = get_opensearch_client()
        os_filters = []

        category = filters.get('category')
        if category:
            os_filters.append({'term': {'category_slug': category}})

        in_stock = filters.get('in_stock')
        if in_stock is True:
            os_filters.append({'term': {'in_stock': True}})

        body = {
            'from': (page - 1) * page_size,
            'size': page_size,
            'query': {
                'bool': {
                    'filter': os_filters,
                    'should': [
                        {'term': {'sku': {'value': query, 'boost': 12}}},
                        {'match_phrase_prefix': {'title': {'query': query, 'boost': 6}}},
                        {
                            'multi_match': {
                                'query': query,
                                'fields': ['title^3', 'description', 'attributes_text'],
                                'fuzziness': 'AUTO',
                            }
                        },
                    ],
                    'minimum_should_match': 1,
                }
            },
        }

        response = client.search(index=settings.SEARCH_INDEX_PRODUCTS, body=body)
        total = response['hits']['total']['value']
        results = []

        for hit in response['hits']['hits']:
            source = hit.get('_source', {})
            results.append(
                {
                    'id': source.get('id'),
                    'title': source.get('title'),
                    'sku': source.get('sku'),
                    'price': source.get('price'),
                    'currency': source.get('currency', 'USD'),
                    'thumbnail': source.get('thumbnail', ''),
                    'in_stock': source.get('in_stock', False),
                    'score': hit.get('_score'),
                }
            )

        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
            },
            'source': 'opensearch',
        }

    def _search_database(self, query: str, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        Product = apps.get_model('catalogue', 'Product')

        queryset = Product.objects.filter(is_public=True).prefetch_related('stockrecords').distinct()

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(upc__icontains=query))

        category = filters.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)

        in_stock = filters.get('in_stock')
        if in_stock is True:
            queryset = queryset.filter(stockrecords__num_in_stock__gt=0)

        paginator = Paginator(queryset.order_by('title'), page_size)
        page_obj = paginator.get_page(page)

        results = [serialize_product_card(product=product) for product in page_obj.object_list]

        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginator.count,
            },
            'source': 'database',
        }
