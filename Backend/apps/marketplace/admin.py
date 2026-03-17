from django.contrib import admin

from .models import SupplierProfile


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'status', 'user', 'partner', 'country_code', 'updated_at')
    list_filter = ('status', 'country_code')
    search_fields = ('company_name', 'contact_name', 'user__email', 'partner__name', 'partner__code')
