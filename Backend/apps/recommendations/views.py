from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RecommendationQuerySerializer
from .services import RecommendationService


class RecommendationAPIView(APIView):
    service = RecommendationService()

    def get(self, request):
        serializer = RecommendationQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        response = self.service.recommend(
            product_id=serializer.validated_data.get('product_id'),
            user_id=serializer.validated_data.get('user_id'),
            limit=serializer.validated_data.get('limit', 12),
        )
        return Response(response)
