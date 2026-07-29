from django.conf import settings
from django.db import models


class PaymentSession(models.Model):
    METHOD_MPESA = 'mpesa'
    METHOD_PESAPAL = 'pesapal'
    METHOD_AIRTEL_MONEY = 'airtel_money'
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD = 'debit_card'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_CASH_ON_DELIVERY = 'cash_on_delivery'

    METHOD_CHOICES = [
        (METHOD_MPESA, 'M-Pesa'),
        (METHOD_PESAPAL, 'Pesapal'),
        (METHOD_AIRTEL_MONEY, 'Airtel Money'),
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_DEBIT_CARD, 'Debit Card'),
        (METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (METHOD_CASH_ON_DELIVERY, 'Cash on Delivery'),
    ]

    STATUS_INITIALIZED = 'initialized'
    STATUS_PENDING = 'pending'
    STATUS_AUTHORIZED = 'authorized'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_INITIALIZED, 'Initialized'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_AUTHORIZED, 'Authorized'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    basket = models.ForeignKey('basket.Basket', null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    order = models.ForeignKey('order.Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    method = models.CharField(max_length=32, choices=METHOD_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_INITIALIZED)
    provider = models.CharField(max_length=64)
    reference = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12)
    payer_email = models.EmailField(blank=True)
    payer_phone = models.CharField(max_length=40, blank=True)
    external_reference = models.CharField(max_length=128, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.reference}:{self.method}:{self.status}'


class PaymentEvent(models.Model):
    KIND_INITIALIZED = 'initialized'
    KIND_PROVIDER_SUBMITTED = 'provider_submitted'
    KIND_NOTIFICATION_RECEIVED = 'notification_received'
    KIND_STATUS_QUERIED = 'status_queried'
    KIND_STATUS_APPLIED = 'status_applied'
    KIND_STATUS_IGNORED = 'status_ignored'
    KIND_GATEWAY_ERROR = 'gateway_error'
    KIND_ORDER_LINKED = 'order_linked'

    KIND_CHOICES = [
        (KIND_INITIALIZED, 'Initialized'),
        (KIND_PROVIDER_SUBMITTED, 'Provider submitted'),
        (KIND_NOTIFICATION_RECEIVED, 'Notification received'),
        (KIND_STATUS_QUERIED, 'Status queried'),
        (KIND_STATUS_APPLIED, 'Status applied'),
        (KIND_STATUS_IGNORED, 'Status ignored'),
        (KIND_GATEWAY_ERROR, 'Gateway error'),
        (KIND_ORDER_LINKED, 'Order linked'),
    ]

    payment_session = models.ForeignKey(PaymentSession, on_delete=models.CASCADE, related_name='events')
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    status_before = models.CharField(max_length=16, blank=True)
    status_after = models.CharField(max_length=16, blank=True)
    external_reference = models.CharField(max_length=128, blank=True)
    message = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['kind', '-created_at']),
            models.Index(fields=['payment_session', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.payment_session.reference}:{self.kind}:{self.status_after or self.status_before}'


class PaymentProviderConfiguration(models.Model):
    PROVIDER_MPESA = 'mpesa'
    PROVIDER_PESAPAL = 'pesapal'
    PROVIDER_AIRTEL_MONEY = 'airtel_money'
    PROVIDER_CARD = 'card'

    PROVIDER_CHOICES = [
        (PROVIDER_MPESA, 'M-Pesa'),
        (PROVIDER_PESAPAL, 'Pesapal'),
        (PROVIDER_AIRTEL_MONEY, 'Airtel Money'),
        (PROVIDER_CARD, 'Card'),
    ]

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, unique=True)
    is_enabled = models.BooleanField(default=True)
    public_config = models.JSONField(default=dict, blank=True)
    secret_config = models.JSONField(default=dict, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_provider_updates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider']

    def __str__(self) -> str:
        return f'{self.provider}:{"enabled" if self.is_enabled else "disabled"}'


class PaymentReconciliation(models.Model):
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
    STATUS_MATCHED = 'matched'
    STATUS_AMOUNT_MISMATCH = 'amount_mismatch'
    STATUS_DUPLICATE = 'duplicate'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REVERSED = 'reversed'
    STATUS_REFUNDED = 'refunded'
    STATUS_MANUAL_REVIEW = 'manual_review'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_MATCHED, 'Matched'),
        (STATUS_AMOUNT_MISMATCH, 'Amount Mismatch'),
        (STATUS_DUPLICATE, 'Duplicate'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REVERSED, 'Reversed'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_MANUAL_REVIEW, 'Manual Review'),
    ]

    payment_session = models.OneToOneField(
        PaymentSession,
        on_delete=models.CASCADE,
        related_name='reconciliation',
    )
    order = models.ForeignKey(
        'order.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='payment_reconciliations',
    )
    provider = models.CharField(max_length=64)
    method = models.CharField(max_length=32)
    merchant_reference = models.CharField(max_length=64)
    provider_reference = models.CharField(max_length=128, blank=True)
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=12)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    issues = models.JSONField(default=list, blank=True)
    raw_provider_payload = models.JSONField(default=dict, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_payment_reconciliations',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    erpnext_sync_status = models.CharField(max_length=16, choices=ERP_STATUS_CHOICES, default=ERP_STATUS_PENDING)
    erpnext_reference = models.CharField(max_length=128, blank=True)
    erpnext_sync_message = models.TextField(blank=True)
    erpnext_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        indexes = [
            models.Index(fields=['status', '-updated_at']),
            models.Index(fields=['provider', 'provider_reference']),
            models.Index(fields=['merchant_reference']),
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.merchant_reference}:{self.status}'


class PaymentRefundLedger(models.Model):
    TYPE_REFUND = 'refund'
    TYPE_CANCELLATION = 'cancellation'
    TYPE_RETURN = 'return'
    TYPE_ADJUSTMENT = 'adjustment'

    TYPE_CHOICES = [
        (TYPE_REFUND, 'Refund'),
        (TYPE_CANCELLATION, 'Cancellation'),
        (TYPE_RETURN, 'Return'),
        (TYPE_ADJUSTMENT, 'Adjustment'),
    ]

    STATUS_REQUESTED = 'requested'
    STATUS_SUBMITTED = 'submitted'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    SCOPE_PARTIAL = 'partial'
    SCOPE_FULL = 'full'

    SCOPE_CHOICES = [
        (SCOPE_PARTIAL, 'Partial'),
        (SCOPE_FULL, 'Full'),
    ]

    COMPLETION_PARTIAL_REQUESTED = 'partial_requested'
    COMPLETION_FULL_REQUESTED = 'full_requested'
    COMPLETION_PARTIAL_SUBMITTED = 'partial_submitted'
    COMPLETION_FULL_SUBMITTED = 'full_submitted'
    COMPLETION_PARTIAL_COMPLETED = 'partial_completed'
    COMPLETION_FULL_COMPLETED = 'full_completed'
    COMPLETION_FAILED = 'failed'
    COMPLETION_CANCELLED = 'cancelled'

    COMPLETION_CHOICES = [
        (COMPLETION_PARTIAL_REQUESTED, 'Partial Requested'),
        (COMPLETION_FULL_REQUESTED, 'Full Requested'),
        (COMPLETION_PARTIAL_SUBMITTED, 'Partial Submitted'),
        (COMPLETION_FULL_SUBMITTED, 'Full Submitted'),
        (COMPLETION_PARTIAL_COMPLETED, 'Partial Completed'),
        (COMPLETION_FULL_COMPLETED, 'Full Completed'),
        (COMPLETION_FAILED, 'Failed'),
        (COMPLETION_CANCELLED, 'Cancelled'),
    ]

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

    payment_session = models.ForeignKey(
        PaymentSession,
        on_delete=models.CASCADE,
        related_name='refund_ledgers',
    )
    reconciliation = models.ForeignKey(
        PaymentReconciliation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='refund_ledgers',
    )
    order = models.ForeignKey(
        'order.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='refund_ledgers',
    )
    line = models.ForeignKey(
        'order.Line',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='refund_ledgers',
    )
    refund_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_REFUND)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    refund_scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default=SCOPE_PARTIAL)
    completion_state = models.CharField(max_length=32, choices=COMPLETION_CHOICES, default=COMPLETION_PARTIAL_REQUESTED)
    refund_reference = models.CharField(max_length=128, unique=True)
    provider_reference = models.CharField(max_length=128, blank=True)
    gateway = models.CharField(max_length=64, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12)
    reason = models.CharField(max_length=255, blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='requested_payment_refunds',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_payment_refunds',
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    erpnext_sync_status = models.CharField(max_length=16, choices=ERP_STATUS_CHOICES, default=ERP_STATUS_PENDING)
    erpnext_reference = models.CharField(max_length=128, blank=True)
    erpnext_sync_message = models.TextField(blank=True)
    erpnext_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['refund_scope', 'completion_state']),
            models.Index(fields=['refund_type', 'status']),
            models.Index(fields=['erpnext_sync_status', '-created_at']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['payment_session', 'status']),
            models.Index(fields=['refund_reference']),
        ]

    def __str__(self) -> str:
        return f'{self.refund_reference}:{self.status}:{self.amount}'


class PaymentReturnCase(models.Model):
    STATUS_REQUESTED = 'requested'
    STATUS_APPROVED = 'approved'
    STATUS_RECEIVED = 'received'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_REFUNDED = 'refunded'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    RESTOCK_PENDING = 'pending'
    RESTOCK_RESTOCK = 'restock'
    RESTOCK_QUARANTINE = 'quarantine'
    RESTOCK_SCRAP = 'scrap'
    RESTOCK_REJECTED = 'rejected'

    RESTOCK_CHOICES = [
        (RESTOCK_PENDING, 'Pending'),
        (RESTOCK_RESTOCK, 'Restock'),
        (RESTOCK_QUARANTINE, 'Quarantine'),
        (RESTOCK_SCRAP, 'Scrap'),
        (RESTOCK_REJECTED, 'Rejected'),
    ]

    return_reference = models.CharField(max_length=128, unique=True)
    payment_session = models.ForeignKey(PaymentSession, on_delete=models.CASCADE, related_name='return_cases')
    reconciliation = models.ForeignKey(PaymentReconciliation, null=True, blank=True, on_delete=models.SET_NULL, related_name='return_cases')
    refund_ledger = models.ForeignKey(PaymentRefundLedger, null=True, blank=True, on_delete=models.SET_NULL, related_name='return_cases')
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE, related_name='return_cases')
    line = models.ForeignKey('order.Line', on_delete=models.CASCADE, related_name='return_cases')
    product = models.ForeignKey('catalogue.Product', null=True, blank=True, on_delete=models.SET_NULL, related_name='return_cases')
    stockrecord = models.ForeignKey('partner.StockRecord', null=True, blank=True, on_delete=models.SET_NULL, related_name='return_cases')
    quantity = models.PositiveIntegerField(default=1)
    accepted_quantity = models.PositiveIntegerField(default=0)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default='KES')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    restock_decision = models.CharField(max_length=32, choices=RESTOCK_CHOICES, default=RESTOCK_PENDING)
    condition_note = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    erpnext_rule = models.CharField(max_length=64, default='credit_note')
    metadata = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='requested_payment_returns')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_payment_returns')
    received_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    restocked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['line', 'status']),
            models.Index(fields=['return_reference']),
        ]

    def __str__(self) -> str:
        return f'{self.return_reference}:{self.status}:{self.refund_amount}'
