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
        ('email_verification', 'Email Verification'),
        ('email_two_factor', 'Email Two Factor'),
        ('password_reset', 'Password Reset'),
        ('password_changed', 'Password Changed'),
        ('quote_request_customer', 'Quote Request Customer'),
        ('quote_request_internal', 'Quote Request Internal'),
        ('order_confirmation', 'Order Confirmation'),
        ('shipping_update', 'Shipping Update'),
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
