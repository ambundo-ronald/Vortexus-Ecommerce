from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.currency import resolve_display_currency

from .serializers import SearchQuerySerializer, SearchSuggestionQuerySerializer
from .services import ProductSearchService


class ProductSearchAPIView(APIView):
    service = ProductSearchService()
    throttle_scope = 'public_search'
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        params = serializer.validated_data
        response = self.service.search(
            query=params.get('q', ''),
            filters={
                'category': params.get('category'),
                'in_stock': params.get('in_stock'),
                'min_price': params.get('min_price'),
                'max_price': params.get('max_price'),
            },
            sort_by=params.get('sort_by', 'relevance'),
            page=params.get('page', 1),
            page_size=params.get('page_size', 24),
            display_currency=resolve_display_currency(request),
        )
        return Response(response)


class ProductSearchSuggestionAPIView(APIView):
    service = ProductSearchService()
    throttle_scope = 'public_search'
    throttle_classes = [ScopedRateThrottle]

    def get(self, request):
        serializer = SearchSuggestionQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            self.service.suggest(
                query=params.get('q', ''),
                category=params.get('category') or None,
                limit=params.get('limit', 8),
            )
        )
