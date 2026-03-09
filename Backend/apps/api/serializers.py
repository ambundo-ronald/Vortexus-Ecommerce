from rest_framework import serializers


class ProductListQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(required=False, allow_blank=True)
    in_stock = serializers.BooleanField(required=False)
    min_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    max_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    sort_by = serializers.ChoiceField(
        required=False,
        default="relevance",
        choices=[
            "relevance",
            "newest",
            "price_asc",
            "price_desc",
            "title_asc",
        ],
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=60, default=24)


class QuoteRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, min_value=1)
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    message = serializers.CharField(max_length=1500)
