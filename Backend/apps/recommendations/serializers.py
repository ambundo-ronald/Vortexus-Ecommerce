from rest_framework import serializers


class RecommendationQuerySerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, min_value=1)
    user_id = serializers.IntegerField(required=False, min_value=1)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=12)
