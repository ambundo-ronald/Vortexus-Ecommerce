from rest_framework import serializers

from apps.integrations.models import IntegrationConnection, SyncEventLog


class IntegrationConnectionSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(required=False, allow_blank=True, write_only=True)
    api_secret = serializers.CharField(required=False, allow_blank=True, write_only=True)
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    has_api_key = serializers.SerializerMethodField(read_only=True)
    has_api_secret = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IntegrationConnection
        fields = [
            'id',
            'name',
            'partner',
            'partner_name',
            'connection_type',
            'base_url',
            'auth_type',
            'api_key',
            'api_secret',
            'has_api_key',
            'has_api_secret',
            'default_company',
            'default_warehouse',
            'poll_interval_minutes',
            'status',
            'is_active',
            'metadata',
            'last_successful_sync_at',
            'last_failed_sync_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['last_successful_sync_at', 'last_failed_sync_at', 'created_at', 'updated_at']

    def get_has_api_key(self, obj):
        return bool(obj.api_key)

    def get_has_api_secret(self, obj):
        return bool(obj.api_secret)

    def create(self, validated_data):
        return IntegrationConnection.objects.create(**validated_data)

    def update(self, instance, validated_data):
        api_key = validated_data.pop('api_key', None)
        api_secret = validated_data.pop('api_secret', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if api_key is not None and api_key != '':
            instance.api_key = api_key
        if api_secret is not None and api_secret != '':
            instance.api_secret = api_secret

        instance.save()
        return instance


class IntegrationPreviewQuerySerializer(serializers.Serializer):
    resource = serializers.ChoiceField(choices=['items', 'stock', 'prices'])
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class ERPNextImportRequestSerializer(serializers.Serializer):
    include_stock = serializers.BooleanField(required=False, default=True)


class SyncEventLogSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source='connection.name', read_only=True)

    class Meta:
        model = SyncEventLog
        fields = [
            'id',
            'connection',
            'connection_name',
            'direction',
            'entity_type',
            'external_reference',
            'status',
            'payload_excerpt',
            'error_message',
            'created_at',
        ]
