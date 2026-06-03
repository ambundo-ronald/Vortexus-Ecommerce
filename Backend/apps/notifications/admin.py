from django.contrib import admin

from .models import EmailConfiguration, EmailNotification, EmailSuppression


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_enabled', 'host', 'from_email', 'password_state', 'updated_by', 'updated_at')
    list_filter = ('provider', 'is_enabled', 'use_tls', 'use_ssl')
    exclude = ('password',)
    readonly_fields = ('created_at', 'updated_at', 'password_state')
    search_fields = ('host', 'from_email', 'username')

    @admin.display(description='Password')
    def password_state(self, obj):
        if not obj.password:
            return 'Not set'
        if obj.password_is_protected:
            return 'Protected'
        return 'Legacy plaintext'


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'recipient', 'status', 'subject', 'sent_at', 'created_at')
    list_filter = ('event_type', 'status')
    search_fields = ('recipient', 'subject', 'related_object_id')
    readonly_fields = ('created_at', 'updated_at', 'sent_at')


@admin.register(EmailSuppression)
class EmailSuppressionAdmin(admin.ModelAdmin):
    list_display = ('email', 'reason', 'source', 'created_by', 'created_at')
    list_filter = ('reason', 'source')
    search_fields = ('email', 'note')
    readonly_fields = ('created_at', 'updated_at')
