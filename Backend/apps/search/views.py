from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SearchQuerySerializer
from .services import ProductSearchService


class ProductSearchAPIView(APIView):
    service = ProductSearchService()

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        params = serializer.validated_data
        response = self.service.search(
            query=params.get('q', ''),
            filters={
                'category': params.get('category'),
                'in_stock': params.get('in_stock'),
            },
            page=params.get('page', 1),
            page_size=params.get('page_size', 24),
        )
        return Response(response)
