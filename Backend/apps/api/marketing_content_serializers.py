from urllib.parse import urlparse

from rest_framework import serializers

from apps.content.models import MarketingBlock


IMAGE_PLACEMENTS = {
    MarketingBlock.PLACEMENT_HOME_HERO,
    MarketingBlock.PLACEMENT_PROMO_BANNER,
    MarketingBlock.PLACEMENT_BRAND_STRIP,
    MarketingBlock.PLACEMENT_TOP_CATEGORY,
}


class MarketingBlockSerializer(serializers.ModelSerializer):
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = MarketingBlock
        fields = [
            'id',
            'title',
            'slug',
            'placement',
            'headline',
            'body',
            'eyebrow',
            'image_url',
            'image_alt',
            'cta_text',
            'cta_url',
            'background_color',
            'text_color',
            'sort_order',
            'is_active',
            'starts_at',
            'ends_at',
            'metadata',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_current', 'created_at', 'updated_at']

    def validate(self, attrs):
        starts_at = attrs.get('starts_at', getattr(self.instance, 'starts_at', None))
        ends_at = attrs.get('ends_at', getattr(self.instance, 'ends_at', None))
        placement = attrs.get('placement', getattr(self.instance, 'placement', ''))
        image_url = (attrs.get('image_url', getattr(self.instance, 'image_url', '')) or '').strip()
        cta_url = (attrs.get('cta_url', getattr(self.instance, 'cta_url', '')) or '').strip()

        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({'ends_at': 'End date must be after start date.'})

        if placement in IMAGE_PLACEMENTS and not image_url:
            raise serializers.ValidationError(
                {'image_url': 'An image is required for this storefront placement.'}
            )

        if placement == MarketingBlock.PLACEMENT_TOP_CATEGORY and not cta_url:
            raise serializers.ValidationError(
                {'cta_url': 'Top categories must link to a storefront category or catalog page.'}
            )

        if cta_url:
            parsed = urlparse(cta_url)
            is_internal = cta_url.startswith('/') and not cta_url.startswith('//')
            is_external = parsed.scheme in {'http', 'https'} and bool(parsed.netloc)
            if not is_internal and not is_external:
                raise serializers.ValidationError(
                    {'cta_url': 'Use a storefront path beginning with / or a full HTTP(S) URL.'}
                )

        return attrs


class PublicMarketingBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingBlock
        fields = [
            'id',
            'title',
            'slug',
            'placement',
            'headline',
            'body',
            'eyebrow',
            'image_url',
            'image_alt',
            'cta_text',
            'cta_url',
            'background_color',
            'text_color',
            'sort_order',
            'metadata',
        ]
