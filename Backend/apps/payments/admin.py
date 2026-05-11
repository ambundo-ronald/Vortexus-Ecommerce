from django.contrib import admin

from .models import PaymentProviderConfiguration, PaymentSession


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'method', 'status', 'amount', 'currency', 'user', 'order', 'updated_at')
    list_filter = ('method', 'status', 'currency')
    search_fields = ('reference', 'external_reference', 'payer_email', 'payer_phone')


@admin.register(PaymentProviderConfiguration)
class PaymentProviderConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_enabled', 'updated_by', 'updated_at')
    list_filter = ('provider', 'is_enabled')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('provider',)
