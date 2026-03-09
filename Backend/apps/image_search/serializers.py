from rest_framework import serializers


class ImageSearchRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    category = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=50, default=12)
