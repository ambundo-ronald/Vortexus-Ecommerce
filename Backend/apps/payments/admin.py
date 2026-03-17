from django.contrib import admin

from .models import PaymentSession


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'method', 'status', 'amount', 'currency', 'user', 'order', 'updated_at')
    list_filter = ('method', 'status', 'currency')
    search_fields = ('reference', 'external_reference', 'payer_email', 'payer_phone')

