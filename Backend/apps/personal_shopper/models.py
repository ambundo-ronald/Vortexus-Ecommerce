import uuid

from django.conf import settings
from django.db import models


class ShopperList(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SHARED = 'shared', 'Shared'
        VIEWED = 'viewed', 'Viewed'
        ADDED_TO_CART = 'added_to_cart', 'Added to cart'
        ARCHIVED = 'archived', 'Archived'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopper_lists')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_shopper_lists')
    title = models.CharField(max_length=160)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT, db_index=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField(blank=True, null=True)
    viewed_at = models.DateTimeField(blank=True, null=True)
    added_to_cart_at = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-date_updated', '-id')

    def __str__(self):
        return f'{self.title} for {self.customer}'


class ShopperListItem(models.Model):
    shopper_list = models.ForeignKey(ShopperList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalogue.Product', on_delete=models.PROTECT, related_name='shopper_list_items')
    quantity = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=300, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('position', 'id')
        constraints = [
            models.UniqueConstraint(fields=('shopper_list', 'product'), name='unique_product_per_shopper_list'),
        ]

