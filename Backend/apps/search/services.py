from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Min, Q
from opensearchpy.exceptions import OpenSearchException

from apps.common.clients import get_opensearch_client
from apps.common.currency import convert_product_payload
from apps.common.products import serialize_product_card


class ProductSearchService:
    def search(
        self,
        query: str,
        filters: dict[str, Any],
        page: int,
        page_size: int,
        sort_by: str = 'relevance',
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        if query.strip():
            try:
                return self._search_opensearch(
                    query=query,
                    filters=filters,
                    page=page,
                    page_size=page_size,
                    sort_by=sort_by,
                    display_currency=display_currency,
                )
            except (OpenSearchException, ValueError, KeyError):
                pass

        return self._search_database(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            display_currency=display_currency,
        )

    def suggest(self, query: str, category: str | None = None, limit: int = 8) -> dict[str, Any]:
        Product = apps.get_model('catalogue', 'Product')
        queryset = Product.objects.filter(is_public=True).exclude(structure='parent')

        cleaned = (query or '').strip()
        if cleaned:
            queryset = queryset.filter(Q(title__icontains=cleaned) | Q(upc__icontains=cleaned))

        if category:
            queryset = queryset.filter(categories__slug=category)

        products = queryset.order_by('title').values('id', 'title', 'upc')[:limit]
        return {
            'results': [
                {
                    'id': item['id'],
                    'title': item['title'],
                    'sku': item['upc'] or '',
                    'type': 'product',
                }
                for item in products
            ],
            'query': cleaned,
        }

    def _search_opensearch(
        self,
        query: str,
        filters: dict[str, Any],
        page: int,
        page_size: int,
        sort_by: str,
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        client = get_opensearch_client()
        os_filters = []

        category = filters.get('category')
        if category:
            os_filters.append({'term': {'category_slug': category}})

        in_stock = filters.get('in_stock')
        if in_stock is True:
            os_filters.append({'term': {'in_stock': True}})

        price_range = {}
        min_price = filters.get('min_price')
        if min_price is not None:
            price_range['gte'] = float(min_price)
        max_price = filters.get('max_price')
        if max_price is not None:
            price_range['lte'] = float(max_price)
        if price_range:
            os_filters.append({'range': {'price': price_range}})

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

        sort = self._opensearch_sort(sort_by)
        if sort:
            body['sort'] = sort

        response = client.search(index=settings.SEARCH_INDEX_PRODUCTS, body=body)
        total = response['hits']['total']['value']
        results = []
        ids = [hit.get('_source', {}).get('id') for hit in response['hits']['hits'] if hit.get('_source', {}).get('id')]
        review_stats = self._review_stats_for_products(ids)

        for hit in response['hits']['hits']:
            source = hit.get('_source', {})
            product_id = source.get('id')
            stats = review_stats.get(product_id, {})
            results.append(
                convert_product_payload(
                    {
                        'id': product_id,
                        'title': source.get('title'),
                        'sku': source.get('sku'),
                        'price': source.get('price'),
                        'base_price': source.get('price'),
                        'currency': source.get('currency', 'USD'),
                        'base_currency': source.get('currency', 'USD'),
                        'thumbnail': source.get('thumbnail', ''),
                        'in_stock': source.get('in_stock', False),
                        'rating': stats.get('rating', source.get('rating')),
                        'review_count': stats.get('review_count', source.get('review_count', 0)),
                        'score': hit.get('_score'),
                    },
                    display_currency,
                )
            )

        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'num_pages': (total + page_size - 1) // page_size if page_size else 1,
                'has_next': page * page_size < total,
            },
            'filters': self._filters_payload(query, filters, sort_by),
            'source': 'opensearch',
        }

    def _search_database(
        self,
        query: str,
        filters: dict[str, Any],
        page: int,
        page_size: int,
        sort_by: str,
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        Product = apps.get_model('catalogue', 'Product')
        Review = apps.get_model('reviews', 'ProductReview')

        queryset = (
            Product.objects.filter(is_public=True)
            .exclude(structure='parent')
            .prefetch_related('stockrecords', 'images', 'categories')
            .annotate(
                list_price=Min('stockrecords__price'),
                average_review_score=Avg(
                    'reviews__score',
                    filter=Q(reviews__status=Review.APPROVED),
                ),
                review_count=Count(
                    'reviews',
                    filter=Q(reviews__status=Review.APPROVED),
                    distinct=True,
                ),
            )
            .distinct()
        )

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(upc__icontains=query) | Q(description__icontains=query))

        category = filters.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)

        in_stock = filters.get('in_stock')
        if in_stock is True:
            queryset = queryset.filter(stockrecords__num_in_stock__gt=0)

        min_price = filters.get('min_price')
        if min_price is not None:
            queryset = queryset.filter(list_price__gte=min_price)

        max_price = filters.get('max_price')
        if max_price is not None:
            queryset = queryset.filter(list_price__lte=max_price)

        queryset = self._database_sort(queryset, sort_by, bool(query.strip()))

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        results = [serialize_product_card(product=product, display_currency=display_currency) for product in page_obj.object_list]

        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginator.count,
                'num_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
            },
            'filters': self._filters_payload(query, filters, sort_by),
            'source': 'database',
        }

    def _database_sort(self, queryset, sort_by: str, has_query: bool):
        if sort_by == 'newest':
            return queryset.order_by('-date_updated', 'title')
        if sort_by == 'price_asc':
            return queryset.order_by('list_price', 'title')
        if sort_by == 'price_desc':
            return queryset.order_by('-list_price', 'title')
        if sort_by == 'title_asc':
            return queryset.order_by('title')
        # Database fallback has no relevance score, so keep a stable title sort.
        return queryset.order_by('title')

    def _opensearch_sort(self, sort_by: str) -> list[dict[str, Any]]:
        if sort_by == 'price_asc':
            return [{'price': {'order': 'asc', 'missing': '_last'}}, {'title.keyword': {'order': 'asc'}}]
        if sort_by == 'price_desc':
            return [{'price': {'order': 'desc', 'missing': '_last'}}, {'title.keyword': {'order': 'asc'}}]
        if sort_by == 'title_asc':
            return [{'title.keyword': {'order': 'asc'}}]
        if sort_by == 'newest':
            return [
                {'date_updated': {'order': 'desc', 'missing': '_last', 'unmapped_type': 'date'}},
                {'title.keyword': {'order': 'asc'}},
            ]
        return []

    def _review_stats_for_products(self, product_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not product_ids:
            return {}
        Review = apps.get_model('reviews', 'ProductReview')
        rows = (
            Review.objects.filter(product_id__in=product_ids, status=Review.APPROVED)
            .values('product_id')
            .annotate(rating=Avg('score'), review_count=Count('id'))
        )
        return {
            row['product_id']: {
                'rating': float(row['rating']) if row['rating'] is not None else None,
                'review_count': row['review_count'] or 0,
            }
            for row in rows
        }

    def _filters_payload(self, query: str, filters: dict[str, Any], sort_by: str) -> dict[str, Any]:
        return {
            'q': (query or '').strip(),
            'category': filters.get('category') or '',
            'in_stock': filters.get('in_stock'),
            'min_price': filters.get('min_price'),
            'max_price': filters.get('max_price'),
            'sort_by': sort_by,
        }
