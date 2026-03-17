from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'status', 'actor_email', 'actor_role', 'target_type', 'target_id')
    list_filter = ('event_type', 'status', 'actor_role', 'target_type', 'created_at')
    search_fields = ('actor_email', 'target_id', 'target_repr', 'message', 'path')
    readonly_fields = (
        'event_type',
        'status',
        'actor',
        'actor_email',
        'actor_role',
        'request_method',
        'path',
        'ip_address',
        'user_agent',
        'target_type',
        'target_id',
        'target_repr',
        'message',
        'metadata',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
