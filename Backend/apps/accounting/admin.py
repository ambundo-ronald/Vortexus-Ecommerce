from django.contrib import admin

from .models import (
    AccountingAccount,
    AccountingBankTransaction,
    AccountingJournalEntry,
    AccountingJournalLine,
    AccountingPaymentLedgerEntry,
    AccountingReconciliationAllocation,
)


class AccountingJournalLineInline(admin.TabularInline):
    model = AccountingJournalLine
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(AccountingAccount)
class AccountingAccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'is_group', 'currency', 'is_active')
    list_filter = ('account_type', 'is_group', 'is_active', 'currency')
    search_fields = ('code', 'name')


@admin.register(AccountingJournalEntry)
class AccountingJournalEntryAdmin(admin.ModelAdmin):
    list_display = ('reference', 'entry_type', 'status', 'posting_date', 'total_debit', 'total_credit', 'currency')
    list_filter = ('entry_type', 'status', 'currency', 'posting_date')
    search_fields = ('reference', 'memo', 'source_object_id')
    readonly_fields = ('total_debit', 'total_credit', 'submitted_at', 'cancelled_at', 'created_at', 'updated_at')
    inlines = [AccountingJournalLineInline]


@admin.register(AccountingPaymentLedgerEntry)
class AccountingPaymentLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'party_type', 'party_id', 'voucher_type', 'voucher_no', 'against_voucher_no', 'amount', 'currency', 'posting_date')
    list_filter = ('account_type', 'party_type', 'voucher_type', 'currency', 'posting_date')
    search_fields = ('party_id', 'party_name', 'voucher_no', 'against_voucher_no')


@admin.register(AccountingBankTransaction)
class AccountingBankTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'bank_account', 'provider', 'reference_number', 'deposit', 'withdrawal', 'currency', 'status')
    list_filter = ('status', 'provider', 'currency', 'transaction_date')
    search_fields = ('reference_number', 'transaction_id', 'description', 'matched_payment_session__reference', 'matched_order__number')
    readonly_fields = ('amount', 'reconciled_at', 'cancelled_at', 'created_at', 'updated_at')


@admin.register(AccountingReconciliationAllocation)
class AccountingReconciliationAllocationAdmin(admin.ModelAdmin):
    list_display = ('bank_transaction', 'payment_session', 'order', 'allocated_amount', 'currency', 'status', 'reconciled_at')
    list_filter = ('status', 'currency', 'reconciled_at')
    search_fields = ('payment_session__reference', 'order__number', 'bank_transaction__reference_number', 'journal_entry__reference')
    readonly_fields = ('created_at', 'updated_at')
