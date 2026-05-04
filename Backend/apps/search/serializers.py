from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.CharField(required=False, allow_blank=True)
    in_stock = serializers.BooleanField(required=False)
    min_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    max_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    sort_by = serializers.ChoiceField(
        required=False,
        default='relevance',
        choices=[
            'relevance',
            'newest',
            'price_asc',
            'price_desc',
            'title_asc',
        ],
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=60, default=24)

    def validate(self, attrs):
        min_price = attrs.get('min_price')
        max_price = attrs.get('max_price')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError({'max_price': 'Max price must be greater than or equal to min price.'})
        return attrs


class SearchSuggestionQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=8)
