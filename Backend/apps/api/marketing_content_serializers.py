from rest_framework import serializers

from apps.content.models import MarketingBlock


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
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({'ends_at': 'End date must be after start date.'})
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
