from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILURE, 'Failure'),
    ]

    event_type = models.CharField(max_length=80, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events',
    )
    actor_email = models.EmailField(blank=True, default='', db_index=True)
    actor_role = models.CharField(max_length=40, blank=True, default='')
    request_method = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='', db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    target_type = models.CharField(max_length=120, blank=True, default='', db_index=True)
    target_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    target_repr = models.CharField(max_length=255, blank=True, default='')
    message = models.CharField(max_length=255, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        actor = self.actor_email or 'anonymous'
        return f'{self.event_type} ({self.status}) by {actor}'


class SearchAnalyticsEvent(models.Model):
    SOURCE_TEXT = 'text'
    SOURCE_SUGGESTION = 'suggestion'
    SOURCE_IMAGE = 'image'
    SOURCE_PRODUCT = 'product'
    SOURCE_CART = 'cart'
    SOURCE_ORDER = 'order'

    EVENT_SEARCH_SUBMITTED = 'search_submitted'
    EVENT_RESULTS_VIEWED = 'search_results_viewed'
    EVENT_NO_RESULTS = 'search_no_results'
    EVENT_SUGGESTION_CLICKED = 'suggestion_clicked'
    EVENT_PRODUCT_CLICKED = 'product_clicked'
    EVENT_IMAGE_SEARCH_SUBMITTED = 'image_search_submitted'
    EVENT_CART_ADDED = 'cart_item_added'
    EVENT_ORDER_CONVERTED = 'order_converted'

    event_type = models.CharField(max_length=60, db_index=True)
    source = models.CharField(max_length=40, blank=True, default='', db_index=True)
    query = models.CharField(max_length=255, blank=True, default='', db_index=True)
    search_context_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    anonymous_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='search_analytics_events',
    )
    user_email = models.EmailField(blank=True, default='', db_index=True)
    category = models.CharField(max_length=120, blank=True, default='', db_index=True)
    brand = models.CharField(max_length=120, blank=True, default='', db_index=True)
    result_count = models.PositiveIntegerField(null=True, blank=True)
    product_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    product_title = models.CharField(max_length=255, blank=True, default='')
    order_number = models.CharField(max_length=64, blank=True, default='', db_index=True)
    path = models.CharField(max_length=255, blank=True, default='')
    ip_hash = models.CharField(max_length=64, blank=True, default='', db_index=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['query', 'created_at']),
            models.Index(fields=['search_context_id', 'event_type']),
        ]

    def __str__(self):
        label = self.query or self.product_title or self.order_number or self.event_type
        return f'{self.event_type}: {label}'
