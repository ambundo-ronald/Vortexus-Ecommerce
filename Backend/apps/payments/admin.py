from django.contrib import admin

from .models import PaymentEvent, PaymentProviderConfiguration, PaymentReconciliation, PaymentRefundLedger, PaymentReturnCase, PaymentSession


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'method', 'status', 'amount', 'currency', 'user', 'order', 'updated_at')
    list_filter = ('method', 'status', 'currency')
    search_fields = ('reference', 'external_reference', 'payer_email', 'payer_phone')


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ('payment_session', 'kind', 'status_before', 'status_after', 'external_reference', 'created_at')
    list_filter = ('kind', 'status_after', 'created_at')
    readonly_fields = ('payment_session', 'kind', 'status_before', 'status_after', 'external_reference', 'message', 'payload', 'created_at')
    search_fields = ('payment_session__reference', 'external_reference', 'message')


@admin.register(PaymentReconciliation)
class PaymentReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        'merchant_reference',
        'provider',
        'status',
        'erpnext_sync_status',
        'expected_amount',
        'paid_amount',
        'fee_amount',
        'settled_amount',
        'currency',
        'order',
        'updated_at',
    )
    list_filter = ('provider', 'method', 'status', 'erpnext_sync_status', 'currency', 'updated_at')
    readonly_fields = (
        'payment_session',
        'order',
        'provider',
        'method',
        'merchant_reference',
        'provider_reference',
        'expected_amount',
        'paid_amount',
        'fee_amount',
        'settled_amount',
        'currency',
        'issues',
        'raw_provider_payload',
        'erpnext_sync_status',
        'erpnext_reference',
        'erpnext_sync_message',
        'erpnext_synced_at',
        'last_checked_at',
        'created_at',
        'updated_at',
    )
    search_fields = ('merchant_reference', 'provider_reference', 'payment_session__payer_email', 'payment_session__payer_phone', 'order__number')


@admin.register(PaymentRefundLedger)
class PaymentRefundLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'refund_reference',
        'refund_type',
        'status',
        'refund_scope',
        'completion_state',
        'erpnext_sync_status',
        'gateway',
        'amount',
        'currency',
        'order',
        'payment_session',
        'requested_at',
    )
    list_filter = ('refund_type', 'status', 'refund_scope', 'completion_state', 'erpnext_sync_status', 'gateway', 'currency', 'requested_at')
    readonly_fields = (
        'payment_session',
        'reconciliation',
        'order',
        'line',
        'refund_type',
        'status',
        'refund_scope',
        'completion_state',
        'refund_reference',
        'provider_reference',
        'gateway',
        'amount',
        'currency',
        'reason',
        'gateway_payload',
        'erpnext_sync_status',
        'erpnext_reference',
        'erpnext_sync_message',
        'erpnext_synced_at',
        'requested_by',
        'reviewed_by',
        'requested_at',
        'processed_at',
        'created_at',
        'updated_at',
    )
    search_fields = ('refund_reference', 'provider_reference', 'payment_session__reference', 'order__number', 'reason')


@admin.register(PaymentReturnCase)
class PaymentReturnCaseAdmin(admin.ModelAdmin):
    list_display = (
        'return_reference',
        'status',
        'restock_decision',
        'quantity',
        'accepted_quantity',
        'refund_amount',
        'currency',
        'order',
        'line',
        'updated_at',
    )
    list_filter = ('status', 'restock_decision', 'currency', 'created_at')
    readonly_fields = (
        'return_reference',
        'payment_session',
        'reconciliation',
        'refund_ledger',
        'order',
        'line',
        'product',
        'stockrecord',
        'quantity',
        'accepted_quantity',
        'refund_amount',
        'currency',
        'erpnext_rule',
        'metadata',
        'requested_by',
        'reviewed_by',
        'received_at',
        'completed_at',
        'restocked_at',
        'created_at',
        'updated_at',
    )
    search_fields = ('return_reference', 'payment_session__reference', 'refund_ledger__refund_reference', 'order__number', 'line__title', 'reason')


@admin.register(PaymentProviderConfiguration)
class PaymentProviderConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_enabled', 'updated_by', 'updated_at')
    list_filter = ('provider', 'is_enabled')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('provider',)
