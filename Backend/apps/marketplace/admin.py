from django.contrib import admin

from .models import SupplierProductSubmission, SupplierProfile


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
