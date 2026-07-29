from django.contrib import admin

from .models import (
    SupplierOrderLineAllocation,
    SupplierPayableAdjustment,
    SupplierPayableLedger,
    SupplierPayoutBatch,
    SupplierPayoutBatchEntry,
    SupplierProductOffer,
    SupplierProductRequest,
    SupplierProductSubmission,
    SupplierProfile,
)


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'status', 'user', 'partner', 'country_code', 'updated_at')
    list_filter = ('status', 'country_code')
    search_fields = ('company_name', 'contact_name', 'user__email', 'partner__name', 'partner__code')


@admin.register(SupplierProductSubmission)
class SupplierProductSubmissionAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'status', 'submitted_by', 'reviewed_by', 'updated_at')
    list_filter = ('status', 'supplier')
    search_fields = ('product__title', 'product__upc', 'supplier__company_name', 'supplier__partner__code')
    readonly_fields = ('submitted_at', 'reviewed_at', 'created_at', 'updated_at')


@admin.register(SupplierProductOffer)
class SupplierProductOfferAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'status', 'supplier_unit_cost', 'available_quantity', 'stockrecord', 'updated_at')
    list_filter = ('status', 'currency', 'supplier')
    search_fields = ('product__title', 'product__upc', 'supplier__company_name', 'supplier__partner__code', 'supplier_sku')
    readonly_fields = ('submitted_at', 'reviewed_at', 'created_at', 'updated_at')


@admin.register(SupplierProductRequest)
class SupplierProductRequestAdmin(admin.ModelAdmin):
    list_display = ('requested_title', 'supplier', 'status', 'linked_product', 'updated_at')
    list_filter = ('status', 'currency', 'supplier')
    search_fields = ('requested_title', 'brand', 'category_hint', 'supplier__company_name', 'supplier__partner__code')
    readonly_fields = ('submitted_at', 'reviewed_at', 'created_at', 'updated_at')


@admin.register(SupplierOrderLineAllocation)
class SupplierOrderLineAllocationAdmin(admin.ModelAdmin):
    list_display = ('order', 'line', 'supplier', 'partner', 'quantity', 'supplier_total_cost', 'gross_margin', 'payout_status')
    list_filter = ('payout_status', 'currency', 'partner', 'supplier')
    search_fields = ('order__number', 'line__title', 'partner__name', 'supplier__company_name', 'payout_reference')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SupplierPayableLedger)
class SupplierPayableLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'line',
        'supplier',
        'partner',
        'status',
        'erpnext_sync_status',
        'quantity',
        'supplier_unit_cost',
        'payable_total',
        'currency',
        'payout_reference',
        'updated_at',
    )
    list_filter = ('status', 'erpnext_sync_status', 'currency', 'partner', 'supplier')
    search_fields = ('order__number', 'line__title', 'partner__name', 'supplier__company_name', 'payout_reference', 'erpnext_reference')
    readonly_fields = ('created_at', 'updated_at', 'metadata', 'erpnext_sync_status', 'erpnext_reference', 'erpnext_sync_message', 'erpnext_synced_at')


@admin.register(SupplierPayableAdjustment)
class SupplierPayableAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        'adjustment_reference',
        'supplier',
        'partner',
        'order',
        'adjustment_type',
        'status',
        'erpnext_sync_status',
        'amount',
        'currency',
        'source_reference',
        'created_at',
    )
    list_filter = ('adjustment_type', 'status', 'erpnext_sync_status', 'currency', 'supplier', 'partner')
    search_fields = (
        'adjustment_reference',
        'source_reference',
        'erpnext_reference',
        'order__number',
        'line__title',
        'supplier__company_name',
        'partner__name',
        'reason',
    )
    readonly_fields = (
        'adjustment_reference',
        'payable',
        'supplier',
        'partner',
        'order',
        'line',
        'adjustment_type',
        'amount',
        'currency',
        'source_reference',
        'metadata',
        'erpnext_sync_status',
        'erpnext_reference',
        'erpnext_sync_message',
        'erpnext_synced_at',
        'created_by',
        'approved_at',
        'applied_at',
        'created_at',
        'updated_at',
    )


class SupplierPayoutBatchEntryInline(admin.TabularInline):
    model = SupplierPayoutBatchEntry
    extra = 0
    readonly_fields = ('payable', 'amount', 'currency', 'created_at')
    can_delete = False


@admin.register(SupplierPayoutBatch)
class SupplierPayoutBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_reference',
        'supplier',
        'partner',
        'status',
        'erpnext_sync_status',
        'entry_count',
        'total_amount',
        'currency',
        'payout_method',
        'payout_reference',
        'evidence_file',
        'created_at',
    )
    list_filter = ('status', 'erpnext_sync_status', 'currency', 'supplier', 'partner')
    search_fields = ('batch_reference', 'supplier__company_name', 'partner__name', 'payout_reference', 'erpnext_reference')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'paid_at', 'erpnext_sync_status', 'erpnext_reference', 'erpnext_sync_message', 'erpnext_synced_at')
    inlines = [SupplierPayoutBatchEntryInline]
