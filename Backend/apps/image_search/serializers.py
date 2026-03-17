from rest_framework import serializers

from apps.common.media import normalize_uploaded_image


class ImageSearchRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    category = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=50, default=12)

    def validate_image(self, value):
        try:
            return normalize_uploaded_image(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
