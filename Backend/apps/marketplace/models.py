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
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
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
