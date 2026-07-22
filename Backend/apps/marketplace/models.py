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
