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

