from django import forms
from django.contrib import admin

from .models import IntegrationConnection, IntegrationMapping, SyncEventLog, SyncJob


class IntegrationConnectionAdminForm(forms.ModelForm):
    api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Leave blank to keep the existing API key.',
    )
    api_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Leave blank to keep the existing API secret.',
    )

    class Meta:
        model = IntegrationConnection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['api_key'].initial = ''
        self.fields['api_secret'].initial = ''
        self.fields['secret_env_prefix'].help_text = 'Used when credential source is Environment Variables. Example: ERPNEXT_NORWA'

    def clean(self):
        cleaned_data = super().clean()
        credential_source = cleaned_data.get('credential_source')
        secret_env_prefix = (cleaned_data.get('secret_env_prefix') or '').strip()
        if credential_source == IntegrationConnection.CREDENTIAL_SOURCE_ENV and not secret_env_prefix:
            self.add_error('secret_env_prefix', 'This field is required when using environment-backed credentials.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        api_key = self.cleaned_data.get('api_key')
        api_secret = self.cleaned_data.get('api_secret')

        if api_key:
            instance.api_key = api_key
        if api_secret:
            instance.api_secret = api_secret

        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(IntegrationConnection)
class IntegrationConnectionAdmin(admin.ModelAdmin):
    form = IntegrationConnectionAdminForm
    list_display = ('name', 'connection_type', 'partner', 'status', 'is_active', 'has_api_key', 'has_api_secret', 'last_successful_sync_at')
    list_filter = ('connection_type', 'status', 'is_active')
    search_fields = ('name', 'base_url', 'partner__name')
    readonly_fields = ('has_api_key', 'has_api_secret', 'last_successful_sync_at', 'last_failed_sync_at', 'created_at', 'updated_at')
    fieldsets = (
        (
            'Connection',
            {
                'fields': (
                    'name',
                    'partner',
                    'connection_type',
                    'base_url',
                    'auth_type',
                    'status',
                    'is_active',
                    'poll_interval_minutes',
                )
            },
        ),
        (
            'Credentials',
            {
                'fields': ('credential_source', 'secret_env_prefix', 'api_key', 'api_secret', 'has_api_key', 'has_api_secret'),
                'description': 'Database-backed credentials are masked. For stronger security, prefer Environment Variables and provide only a prefix such as ERPNEXT_NORWA.',
            },
        ),
        (
            'Defaults',
            {
                'fields': ('default_company', 'default_warehouse', 'metadata'),
            },
        ),
        (
            'Sync Status',
            {
                'fields': ('last_successful_sync_at', 'last_failed_sync_at', 'created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(boolean=True, description='API key set')
    def has_api_key(self, obj):
        return obj.has_resolved_api_key()

    @admin.display(boolean=True, description='API secret set')
    def has_api_secret(self, obj):
        return obj.has_resolved_api_secret()


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

