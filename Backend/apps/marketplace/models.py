from django.conf import settings
from django.db import models


class SupplierProfile(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_profile')
    partner = models.OneToOneField('partner.Partner', on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    status_note = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_supplier_profiles',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name', 'id']

    def __str__(self) -> str:
        return f'{self.company_name} ({self.status})'

    @property
    def is_active_supplier(self) -> bool:
        return self.status == self.STATUS_APPROVED


class SupplierOrderGroup(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_PACKED = 'packed'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PARTIALLY_SHIPPED = 'partially_shipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_PACKED, 'Packed'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_PARTIALLY_SHIPPED, 'Partially Shipped'),
    ]

    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, related_name='supplier_groups')
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, related_name='order_groups')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    line_count = models.PositiveIntegerField(default=0)
    item_count = models.PositiveIntegerField(default=0)
    total_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tracking_reference = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_id', 'partner_id']
        constraints = [
            models.UniqueConstraint(fields=['order', 'partner'], name='uniq_supplier_group_order_partner'),
        ]

    def __str__(self) -> str:
        return f'{self.order.number}::{self.partner.name}'


class SupplierProductOffer(models.Model):
    STATUS_PENDING_REVIEW = 'pending_review'
    STATUS_APPROVED = 'approved'
    STATUS_CHANGES_REQUESTED = 'changes_requested'
    STATUS_REJECTED = 'rejected'
    STATUS_SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_CHANGES_REQUESTED, 'Changes Requested'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='product_offers')
    product = models.ForeignKey('catalogue.Product', on_delete=models.CASCADE, related_name='supplier_offers')
    stockrecord = models.OneToOneField(
        'partner.StockRecord',
        on_delete=models.SET_NULL,
        related_name='supplier_offer',
        null=True,
        blank=True,
    )
    supplier_sku = models.CharField(max_length=128, blank=True)
    supplier_unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12, default='KES')
    available_quantity = models.PositiveIntegerField(default=0)
    lead_time_days = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='submitted_supplier_offers',
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_supplier_offers',
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['supplier', 'product'], name='uniq_supplier_offer_supplier_product'),
        ]
        indexes = [
            models.Index(fields=['supplier', 'status'], name='supp_offer_supplier_status'),
            models.Index(fields=['product', 'status'], name='supp_offer_product_status'),
            models.Index(fields=['status', 'updated_at'], name='supp_offer_status_updated'),
        ]

    def __str__(self) -> str:
        return f'{self.supplier.company_name}::{self.product_id}::{self.status}'


class SupplierProductRequest(models.Model):
    STATUS_PENDING_REVIEW = 'pending_review'
    STATUS_APPROVED = 'approved'
    STATUS_CHANGES_REQUESTED = 'changes_requested'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_CHANGES_REQUESTED, 'Changes Requested'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='product_requests')
    requested_title = models.CharField(max_length=255)
    brand = models.CharField(max_length=128, blank=True)
    category_hint = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    specs = models.JSONField(default=dict, blank=True)
    supplier_sku = models.CharField(max_length=128, blank=True)
    supplier_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=12, default='KES')
    available_quantity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    linked_product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, related_name='supplier_requests', null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='submitted_supplier_product_requests',
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_supplier_product_requests',
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        indexes = [
            models.Index(fields=['supplier', 'status'], name='supp_req_supplier_status'),
            models.Index(fields=['status', 'updated_at'], name='supp_req_status_updated'),
        ]

    def __str__(self) -> str:
        return f'{self.requested_title}::{self.supplier.company_name}::{self.status}'


class SupplierOrderLineAllocation(models.Model):
    PAYOUT_PENDING = 'pending'
    PAYOUT_APPROVED = 'approved'
    PAYOUT_PAID = 'paid'
    PAYOUT_CANCELLED = 'cancelled'

    PAYOUT_STATUS_CHOICES = [
        (PAYOUT_PENDING, 'Pending'),
        (PAYOUT_APPROVED, 'Approved'),
        (PAYOUT_PAID, 'Paid'),
        (PAYOUT_CANCELLED, 'Cancelled'),
    ]

    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, related_name='supplier_allocations')
    line = models.ForeignKey('order.Line', on_delete=models.CASCADE, related_name='supplier_allocations')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.SET_NULL, related_name='order_line_allocations', null=True, blank=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, related_name='order_line_allocations')
    product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, related_name='supplier_order_allocations', null=True, blank=True)
    stockrecord = models.ForeignKey('partner.StockRecord', on_delete=models.SET_NULL, related_name='order_line_allocations', null=True, blank=True)
    supplier_offer = models.ForeignKey(SupplierProductOffer, on_delete=models.SET_NULL, related_name='order_line_allocations', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    customer_unit_price_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    customer_unit_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier_total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_margin = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    payout_status = models.CharField(max_length=32, choices=PAYOUT_STATUS_CHOICES, default=PAYOUT_PENDING)
    payout_reference = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_id', 'line_id', 'id']
        indexes = [
            models.Index(fields=['partner', 'payout_status'], name='supp_alloc_partner_payout'),
            models.Index(fields=['supplier', 'payout_status'], name='supp_alloc_supplier_payout'),
            models.Index(fields=['order', 'partner'], name='supp_alloc_order_partner'),
        ]

    def __str__(self) -> str:
        return f'{self.order.number} line={self.line_id} partner={self.partner_id} payout={self.supplier_total_cost}'


class SupplierPayableLedger(models.Model):
    ERP_STATUS_PENDING = 'pending'
    ERP_STATUS_SYNCED = 'synced'
    ERP_STATUS_SKIPPED = 'skipped'
    ERP_STATUS_FAILED = 'failed'

    ERP_STATUS_CHOICES = [
        (ERP_STATUS_PENDING, 'Pending'),
        (ERP_STATUS_SYNCED, 'Synced'),
        (ERP_STATUS_SKIPPED, 'Skipped'),
        (ERP_STATUS_FAILED, 'Failed'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PAYABLE = 'payable'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_APPROVED = 'approved'
    STATUS_PAID = 'paid'
    STATUS_DISPUTED = 'disputed'
    STATUS_REVERSED = 'reversed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAYABLE, 'Payable'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
        (STATUS_DISPUTED, 'Disputed'),
        (STATUS_REVERSED, 'Reversed'),
    ]

    allocation = models.OneToOneField(
        SupplierOrderLineAllocation,
        on_delete=models.CASCADE,
        related_name='payable_ledger',
    )
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.SET_NULL, related_name='payable_ledgers', null=True, blank=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, related_name='payable_ledgers')
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, related_name='supplier_payable_ledgers')
    line = models.ForeignKey('order.Line', on_delete=models.CASCADE, related_name='supplier_payable_ledgers')
    product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, related_name='supplier_payable_ledgers', null=True, blank=True)
    supplier_offer = models.ForeignKey(SupplierProductOffer, on_delete=models.SET_NULL, related_name='payable_ledgers', null=True, blank=True)
    stockrecord = models.ForeignKey('partner.StockRecord', on_delete=models.SET_NULL, related_name='supplier_payable_ledgers', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    supplier_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payable_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    source_status = models.CharField(max_length=64, blank=True)
    payout_reference = models.CharField(max_length=128, blank=True)
    reversal_reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    erpnext_sync_status = models.CharField(max_length=16, choices=ERP_STATUS_CHOICES, default=ERP_STATUS_PENDING)
    erpnext_reference = models.CharField(max_length=128, blank=True)
    erpnext_sync_message = models.TextField(blank=True)
    erpnext_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_id', 'line_id', 'id']
        indexes = [
            models.Index(fields=['partner', 'status'], name='supp_pay_partner_status'),
            models.Index(fields=['supplier', 'status'], name='supp_pay_supplier_status'),
            models.Index(fields=['order', 'status'], name='supp_pay_order_status'),
            models.Index(fields=['status', 'updated_at'], name='supp_pay_status_updated'),
            models.Index(fields=['erpnext_sync_status', 'updated_at'], name='supp_pay_erp_status'),
        ]

    def __str__(self) -> str:
        return f'{self.order.number} line={self.line_id} supplier={self.supplier_id} payable={self.payable_total}'


class SupplierPayoutBatch(models.Model):
    ERP_STATUS_PENDING = 'pending'
    ERP_STATUS_SYNCED = 'synced'
    ERP_STATUS_SKIPPED = 'skipped'
    ERP_STATUS_FAILED = 'failed'

    ERP_STATUS_CHOICES = [
        (ERP_STATUS_PENDING, 'Pending'),
        (ERP_STATUS_SYNCED, 'Synced'),
        (ERP_STATUS_SKIPPED, 'Skipped'),
        (ERP_STATUS_FAILED, 'Failed'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_APPROVED = 'approved'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING_APPROVAL, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    batch_reference = models.CharField(max_length=64, unique=True)
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.SET_NULL, related_name='payout_batches', null=True, blank=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, related_name='supplier_payout_batches', null=True, blank=True)
    currency = models.CharField(max_length=12, default='KES')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    entry_count = models.PositiveIntegerField(default=0)
    payout_method = models.CharField(max_length=64, blank=True)
    payout_reference = models.CharField(max_length=128, blank=True)
    evidence_url = models.URLField(blank=True)
    evidence_file = models.FileField(upload_to='finance/payout-evidence/%Y/%m/', blank=True)
    notes = models.TextField(blank=True)
    erpnext_sync_status = models.CharField(max_length=16, choices=ERP_STATUS_CHOICES, default=ERP_STATUS_PENDING)
    erpnext_reference = models.CharField(max_length=128, blank=True)
    erpnext_sync_message = models.TextField(blank=True)
    erpnext_synced_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='created_supplier_payout_batches', null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='approved_supplier_payout_batches', null=True, blank=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='paid_supplier_payout_batches', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='supp_payout_status_created'),
            models.Index(fields=['supplier', 'status'], name='supp_payout_supplier_status'),
            models.Index(fields=['batch_reference'], name='supp_payout_reference'),
            models.Index(fields=['erpnext_sync_status', '-created_at'], name='supp_payout_erp_status'),
        ]

    def __str__(self) -> str:
        return f'{self.batch_reference}:{self.status}:{self.total_amount}'


class SupplierPayoutBatchEntry(models.Model):
    batch = models.ForeignKey(SupplierPayoutBatch, on_delete=models.CASCADE, related_name='entries')
    payable = models.OneToOneField(SupplierPayableLedger, on_delete=models.PROTECT, related_name='payout_batch_entry')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['batch_id', 'id']
        indexes = [
            models.Index(fields=['batch', 'currency'], name='supp_payout_entry_batch'),
        ]

    def __str__(self) -> str:
        return f'{self.batch.batch_reference}:{self.payable_id}:{self.amount}'


class SupplierPayableAdjustment(models.Model):
    ERP_STATUS_PENDING = 'pending'
    ERP_STATUS_SYNCED = 'synced'
    ERP_STATUS_SKIPPED = 'skipped'
    ERP_STATUS_FAILED = 'failed'

    ERP_STATUS_CHOICES = [
        (ERP_STATUS_PENDING, 'Pending'),
        (ERP_STATUS_SYNCED, 'Synced'),
        (ERP_STATUS_SKIPPED, 'Skipped'),
        (ERP_STATUS_FAILED, 'Failed'),
    ]

    TYPE_DEBIT = 'debit'
    TYPE_CREDIT = 'credit'
    TYPE_REVERSAL = 'reversal'

    TYPE_CHOICES = [
        (TYPE_DEBIT, 'Debit'),
        (TYPE_CREDIT, 'Credit'),
        (TYPE_REVERSAL, 'Reversal'),
    ]

    STATUS_PENDING_REVIEW = 'pending_review'
    STATUS_APPROVED = 'approved'
    STATUS_APPLIED = 'applied'
    STATUS_VOID = 'void'

    STATUS_CHOICES = [
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_APPLIED, 'Applied'),
        (STATUS_VOID, 'Void'),
    ]

    adjustment_reference = models.CharField(max_length=64, unique=True)
    payable = models.ForeignKey(SupplierPayableLedger, on_delete=models.CASCADE, related_name='adjustments')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.SET_NULL, related_name='payable_adjustments', null=True, blank=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, related_name='supplier_payable_adjustments')
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, related_name='supplier_payable_adjustments')
    line = models.ForeignKey('order.Line', on_delete=models.CASCADE, related_name='supplier_payable_adjustments')
    adjustment_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_DEBIT)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12, default='KES')
    reason = models.CharField(max_length=255, blank=True)
    source_reference = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    erpnext_sync_status = models.CharField(max_length=16, choices=ERP_STATUS_CHOICES, default=ERP_STATUS_PENDING)
    erpnext_reference = models.CharField(max_length=128, blank=True)
    erpnext_sync_message = models.TextField(blank=True)
    erpnext_synced_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='created_supplier_payable_adjustments', null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='approved_supplier_payable_adjustments', null=True, blank=True)
    applied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='applied_supplier_payable_adjustments', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['supplier', 'status'], name='supp_adj_supplier_status'),
            models.Index(fields=['partner', 'status'], name='supp_adj_partner_status'),
            models.Index(fields=['order', 'status'], name='supp_adj_order_status'),
            models.Index(fields=['adjustment_reference'], name='supp_adj_reference'),
        ]

    def __str__(self) -> str:
        return f'{self.adjustment_reference}:{self.adjustment_type}:{self.amount}'


class SupplierProductSubmission(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PENDING_REVIEW = 'pending_review'
    STATUS_CHANGES_REQUESTED = 'changes_requested'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_CHANGES_REQUESTED, 'Changes Requested'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    product = models.OneToOneField('catalogue.Product', on_delete=models.CASCADE, related_name='supplier_submission')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='product_submissions')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='supplier_product_submissions',
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_supplier_product_submissions',
        null=True,
        blank=True,
    )
    supplier_note = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        indexes = [
            models.Index(fields=['status', 'updated_at']),
            models.Index(fields=['supplier', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.product_id}::{self.supplier.company_name}::{self.status}'
