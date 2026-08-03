from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class AccountingAccount(models.Model):
    TYPE_ASSET = 'asset'
    TYPE_LIABILITY = 'liability'
    TYPE_EQUITY = 'equity'
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'

    TYPE_CHOICES = [
        (TYPE_ASSET, 'Asset'),
        (TYPE_LIABILITY, 'Liability'),
        (TYPE_EQUITY, 'Equity'),
        (TYPE_INCOME, 'Income'),
        (TYPE_EXPENSE, 'Expense'),
    ]

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    account_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children')
    is_group = models.BooleanField(default=False)
    currency = models.CharField(max_length=12, default='KES')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['account_type', 'is_active']),
            models.Index(fields=['parent', 'code']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'


class AccountingJournalEntry(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    TYPE_SALES = 'sales'
    TYPE_PAYMENT = 'payment'
    TYPE_SUPPLIER_PAYABLE = 'supplier_payable'
    TYPE_SUPPLIER_PAYOUT = 'supplier_payout'
    TYPE_REFUND = 'refund'
    TYPE_ADJUSTMENT = 'adjustment'
    TYPE_MANUAL = 'manual'

    TYPE_CHOICES = [
        (TYPE_SALES, 'Sales'),
        (TYPE_PAYMENT, 'Payment'),
        (TYPE_SUPPLIER_PAYABLE, 'Supplier Payable'),
        (TYPE_SUPPLIER_PAYOUT, 'Supplier Payout'),
        (TYPE_REFUND, 'Refund'),
        (TYPE_ADJUSTMENT, 'Adjustment'),
        (TYPE_MANUAL, 'Manual'),
    ]

    reference = models.CharField(max_length=80, unique=True)
    entry_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_MANUAL)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    posting_date = models.DateField()
    memo = models.TextField(blank=True)
    source_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    source_object_id = models.CharField(max_length=64, blank=True)
    source = GenericForeignKey('source_content_type', 'source_object_id')
    total_debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='submitted_accounting_journals')
    submitted_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cancelled_accounting_journals')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posting_date', '-id']
        indexes = [
            models.Index(fields=['status', '-posting_date']),
            models.Index(fields=['entry_type', '-posting_date']),
            models.Index(fields=['source_content_type', 'source_object_id']),
        ]

    def clean(self):
        if self.status == self.STATUS_SUBMITTED and self.total_debit != self.total_credit:
            raise ValidationError('Submitted journal entries must have equal debit and credit totals.')

    def __str__(self):
        return f'{self.reference}:{self.status}'


class AccountingJournalLine(models.Model):
    journal_entry = models.ForeignKey(AccountingJournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(AccountingAccount, on_delete=models.PROTECT, related_name='journal_lines')
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    party_type = models.CharField(max_length=32, blank=True)
    party_id = models.CharField(max_length=64, blank=True)
    party_name = models.CharField(max_length=160, blank=True)
    against_account = models.CharField(max_length=160, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['journal_entry_id', 'id']
        indexes = [
            models.Index(fields=['account', 'currency']),
            models.Index(fields=['party_type', 'party_id']),
        ]

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError('Debit and credit amounts cannot be negative.')
        if self.debit and self.credit:
            raise ValidationError('A journal line cannot have both debit and credit values.')

    def __str__(self):
        return f'{self.journal_entry.reference}:{self.account.code}:{self.debit}/{self.credit}'


class AccountingPaymentLedgerEntry(models.Model):
    TYPE_RECEIVABLE = 'receivable'
    TYPE_PAYABLE = 'payable'

    TYPE_CHOICES = [
        (TYPE_RECEIVABLE, 'Receivable'),
        (TYPE_PAYABLE, 'Payable'),
    ]

    account_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    account = models.ForeignKey(AccountingAccount, on_delete=models.PROTECT, related_name='payment_ledger_entries')
    party_type = models.CharField(max_length=32)
    party_id = models.CharField(max_length=64)
    party_name = models.CharField(max_length=160, blank=True)
    voucher_type = models.CharField(max_length=64)
    voucher_no = models.CharField(max_length=128)
    against_voucher_type = models.CharField(max_length=64, blank=True)
    against_voucher_no = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=12, default='KES')
    posting_date = models.DateField()
    journal_entry = models.ForeignKey(AccountingJournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_ledger_entries')
    source_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    source_object_id = models.CharField(max_length=64, blank=True)
    source = GenericForeignKey('source_content_type', 'source_object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posting_date', '-id']
        indexes = [
            models.Index(fields=['account_type', 'party_type', 'party_id']),
            models.Index(fields=['voucher_type', 'voucher_no']),
            models.Index(fields=['against_voucher_type', 'against_voucher_no']),
            models.Index(fields=['source_content_type', 'source_object_id']),
        ]

    def __str__(self):
        return f'{self.account_type}:{self.party_type}:{self.party_id}:{self.amount}'


class AccountingBankTransaction(models.Model):
    STATUS_UNRECONCILED = 'unreconciled'
    STATUS_RECONCILED = 'reconciled'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_UNRECONCILED, 'Unreconciled'),
        (STATUS_RECONCILED, 'Reconciled'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    SOURCE_MANUAL = 'manual'
    SOURCE_IMPORT = 'import'
    SOURCE_GATEWAY = 'gateway'

    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'Manual'),
        (SOURCE_IMPORT, 'Import'),
        (SOURCE_GATEWAY, 'Gateway'),
    ]

    transaction_date = models.DateField(db_index=True)
    bank_account = models.CharField(max_length=160, default='Cash and Bank')
    provider = models.CharField(max_length=64, blank=True)
    reference_number = models.CharField(max_length=128, blank=True, db_index=True)
    transaction_id = models.CharField(max_length=128, blank=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    deposit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    withdrawal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_UNRECONCILED, db_index=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    matched_payment_session = models.ForeignKey('payments.PaymentSession', null=True, blank=True, on_delete=models.SET_NULL, related_name='bank_transactions')
    matched_order = models.ForeignKey('order.Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='bank_transactions')
    clearance_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_bank_transactions')
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reconciled_bank_transactions')
    reconciled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cancelled_bank_transactions')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-id']
        indexes = [
            models.Index(fields=['status', '-transaction_date']),
            models.Index(fields=['provider', 'reference_number']),
            models.Index(fields=['matched_order', 'status']),
            models.Index(fields=['matched_payment_session', 'status']),
        ]

    @property
    def amount(self):
        return self.deposit - self.withdrawal

    def clean(self):
        if self.deposit < 0 or self.withdrawal < 0:
            raise ValidationError('Deposit and withdrawal cannot be negative.')
        if self.deposit and self.withdrawal:
            raise ValidationError('A bank transaction cannot be both deposit and withdrawal.')

    def __str__(self):
        return f'{self.transaction_date}:{self.reference_number or self.transaction_id}:{self.amount}'


class AccountingReconciliationAllocation(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_RECONCILED = 'reconciled'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_RECONCILED, 'Reconciled'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    bank_transaction = models.ForeignKey(AccountingBankTransaction, null=True, blank=True, on_delete=models.SET_NULL, related_name='allocations')
    payment_session = models.ForeignKey('payments.PaymentSession', null=True, blank=True, on_delete=models.SET_NULL, related_name='accounting_allocations')
    order = models.ForeignKey('order.Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='accounting_allocations')
    journal_entry = models.ForeignKey(AccountingJournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name='reconciliation_allocations')
    allocated_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=12, default='KES')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    note = models.TextField(blank=True)
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='accounting_reconciliations')
    reconciled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['payment_session', 'status']),
        ]

    def clean(self):
        if self.allocated_amount <= 0:
            raise ValidationError('Allocated amount must be greater than zero.')

    def __str__(self):
        return f'{self.bank_transaction_id}:{self.payment_session_id}:{self.allocated_amount}:{self.status}'
