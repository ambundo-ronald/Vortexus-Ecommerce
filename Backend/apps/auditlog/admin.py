from django.contrib import admin

from .models import AuditLog, SearchAnalyticsEvent


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


@admin.register(SearchAnalyticsEvent)
class SearchAnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'source', 'query', 'result_count', 'product_id', 'user_email')
    list_filter = ('event_type', 'source', 'created_at')
    search_fields = ('query', 'search_context_id', 'anonymous_id', 'user_email', 'product_title', 'order_number')
    readonly_fields = (
        'event_type',
        'source',
        'query',
        'search_context_id',
        'anonymous_id',
        'user',
        'user_email',
        'category',
        'brand',
        'result_count',
        'product_id',
        'product_title',
        'order_number',
        'path',
        'ip_hash',
        'user_agent',
        'metadata',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
