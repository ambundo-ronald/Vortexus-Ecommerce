from django.contrib import admin

from .models import (
    SupplierOrderLineAllocation,
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
