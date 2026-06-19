from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    country_code = models.CharField(max_length=2, blank=True)
    preferred_currency = models.CharField(max_length=3, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=120, blank=True)
    receive_order_updates = models.BooleanField(default=True)
    receive_marketing_emails = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    two_factor_email_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user_id']

    def __str__(self):
        return f'CustomerProfile(user_id={self.user_id})'


class EmailTwoFactorChallenge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_two_factor_challenges',
    )
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'EmailTwoFactorChallenge(user_id={self.user_id})'


class DeliveryLocation(models.Model):
    user_address = models.OneToOneField(
        'address.UserAddress',
        on_delete=models.CASCADE,
        related_name='delivery_location',
        blank=True,
        null=True,
    )
    shipping_address = models.OneToOneField(
        'order.ShippingAddress',
        on_delete=models.CASCADE,
        related_name='delivery_location',
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    label = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        target = self.shipping_address_id or self.user_address_id or 'unassigned'
        return f'DeliveryLocation({target}: {self.latitude}, {self.longitude})'
