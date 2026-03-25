from django.contrib import admin

from .models import IntegrationConnection, IntegrationMapping, SyncEventLog, SyncJob


@admin.register(IntegrationConnection)
class IntegrationConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'connection_type', 'partner', 'status', 'is_active', 'last_successful_sync_at')
    list_filter = ('connection_type', 'status', 'is_active')
    search_fields = ('name', 'base_url', 'partner__name')


@admin.register(IntegrationMapping)
class IntegrationMappingAdmin(admin.ModelAdmin):
    list_display = ('connection', 'entity_type', 'external_id', 'internal_model', 'internal_id')
    list_filter = ('entity_type', 'connection')
    search_fields = ('external_id', 'internal_id', 'connection__name')


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ('connection', 'job_type', 'direction', 'status', 'created_at', 'started_at', 'finished_at')
    list_filter = ('job_type', 'direction', 'status', 'connection')
    search_fields = ('connection__name', 'cursor', 'error_message')


@admin.register(SyncEventLog)
class SyncEventLogAdmin(admin.ModelAdmin):
    list_display = ('connection', 'direction', 'entity_type', 'external_reference', 'status', 'created_at')
    list_filter = ('direction', 'status', 'entity_type', 'connection')
    search_fields = ('external_reference', 'error_message', 'connection__name')

