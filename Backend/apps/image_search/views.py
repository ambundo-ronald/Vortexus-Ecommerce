from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.currency import resolve_display_currency

from .serializers import ImageSearchRequestSerializer
from .services import ImageSearchService


class ImageSearchAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    service = ImageSearchService()
    throttle_scope = 'image_search'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = ImageSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            response = self.service.search_similar(
                image_file=data['image'],
                top_k=data.get('top_k', 12),
                category=data.get('category') or None,
                display_currency=resolve_display_currency(request),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response)
