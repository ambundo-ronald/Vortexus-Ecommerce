from django.db import models
from django.conf import settings

from .secret_store import is_sealed_secret, seal_secret, unseal_secret


class EmailConfiguration(models.Model):
    PROVIDER_SMTP = 'smtp'

    PROVIDER_CHOICES = [
        (PROVIDER_SMTP, 'SMTP'),
    ]

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default=PROVIDER_SMTP, unique=True)
    is_enabled = models.BooleanField(default=False)
    host = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(default=587)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=1024, blank=True)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    timeout_seconds = models.PositiveIntegerField(default=30)
    from_email = models.EmailField(blank=True)
    reply_to_email = models.EmailField(blank=True)
    sales_recipients = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='email_configuration_updates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider']

    def __str__(self) -> str:
        return f'{self.provider}:{"enabled" if self.is_enabled else "disabled"}'

    def set_password_secret(self, raw_password: str) -> None:
        self.password = seal_secret(raw_password)

    def get_password_secret(self) -> str:
        return unseal_secret(self.password)

    @property
    def password_is_protected(self) -> bool:
        return is_sealed_secret(self.password)

    def save(self, *args, **kwargs):
        if self.password:
            self.password = seal_secret(self.password)
        super().save(*args, **kwargs)


class EmailNotification(models.Model):
    EVENT_CHOICES = [
        ('account_registered', 'Account Registered'),
        ('account_reactivation_request', 'Account Reactivation Request'),
        ('email_verification', 'Email Verification'),
        ('email_two_factor', 'Email Two Factor'),
        ('password_reset', 'Password Reset'),
        ('password_changed', 'Password Changed'),
        ('quote_request_customer', 'Quote Request Customer'),
        ('quote_request_internal', 'Quote Request Internal'),
        ('order_confirmation', 'Order Confirmation'),
        ('shipping_update', 'Shipping Update'),
        ('supplier_application_submitted', 'Supplier Application Submitted'),
        ('supplier_status_changed', 'Supplier Status Changed'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    event_type = models.CharField(max_length=64, choices=EVENT_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    related_object_type = models.CharField(max_length=64, blank=True)
    related_object_id = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.event_type}:{self.recipient}:{self.status}'


class EmailSuppression(models.Model):
    REASON_CHOICES = [
        ('bounce', 'Bounce'),
        ('complaint', 'Complaint'),
        ('manual', 'Manual'),
        ('unsubscribe', 'Unsubscribe'),
    ]

    email = models.EmailField(unique=True)
    reason = models.CharField(max_length=32, choices=REASON_CHOICES, default='manual')
    source = models.CharField(max_length=64, blank=True)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='email_suppressions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['email']

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.email}:{self.reason}'


class AdminNotification(models.Model):
    SEVERITY_INFO = 'info'
    SEVERITY_SUCCESS = 'success'
    SEVERITY_WARNING = 'warning'
    SEVERITY_ERROR = 'error'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_SUCCESS, 'Success'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_ERROR, 'Error'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_notifications')
    event_type = models.CharField(max_length=80)
    event_key = models.CharField(max_length=160, blank=True)
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default=SEVERITY_INFO)
    action_url = models.CharField(max_length=255, blank=True)
    related_object_type = models.CharField(max_length=64, blank=True)
    related_object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'event_key'], condition=~models.Q(event_key=''), name='unique_admin_notification_event_per_user'),
        ]
        indexes = [
            models.Index(fields=['user', 'read_at', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}:{self.event_type}:{self.title}'


class PushSubscription(models.Model):
    CHANNEL_ADMIN = 'admin'
    CHANNEL_STOREFRONT = 'storefront'

    CHANNEL_CHOICES = [
        (CHANNEL_ADMIN, 'Admin'),
        (CHANNEL_STOREFRONT, 'Storefront'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')
    channel = models.CharField(max_length=32, choices=CHANNEL_CHOICES, default=CHANNEL_STOREFRONT)
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    browser = models.CharField(max_length=120, blank=True)
    user_agent = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'channel', 'is_enabled']),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}:{self.channel}:{self.endpoint[:32]}'


class PushDeliveryLog(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    subscription = models.ForeignKey(PushSubscription, null=True, blank=True, on_delete=models.SET_NULL, related_name='delivery_logs')
    notification = models.ForeignKey(AdminNotification, null=True, blank=True, on_delete=models.SET_NULL, related_name='push_delivery_logs')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    endpoint_hash = models.CharField(max_length=64, blank=True)
    event_type = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=160, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.event_type}:{self.status}'
