from django.db import models


class EmailNotification(models.Model):
    EVENT_CHOICES = [
        ('account_registered', 'Account Registered'),
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

