from rest_framework import serializers


class AuditLogSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    actor_id = serializers.SerializerMethodField()
    actor_email = serializers.CharField(read_only=True)
    actor_role = serializers.CharField(read_only=True)
    request_method = serializers.CharField(read_only=True)
    path = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    target_type = serializers.CharField(read_only=True)
    target_id = serializers.CharField(read_only=True)
    target_repr = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    metadata = serializers.JSONField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_actor_id(self, obj):
        return obj.actor_id
