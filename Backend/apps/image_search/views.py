from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ImageSearchRequestSerializer
from .services import ImageSearchService


class ImageSearchAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    service = ImageSearchService()

    def post(self, request):
        serializer = ImageSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            response = self.service.search_similar(
                image_file=data['image'],
                top_k=data.get('top_k', 12),
                category=data.get('category') or None,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response)
