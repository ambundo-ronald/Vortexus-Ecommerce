from django.conf import settings
from django.db import models


class IntegrationConnection(models.Model):
    TYPE_ERPNEXT = 'erpnext'

    TYPE_CHOICES = [
        (TYPE_ERPNEXT, 'ERPNext'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_ERROR = 'error'
    STATUS_DISABLED = 'disabled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ERROR, 'Error'),
        (STATUS_DISABLED, 'Disabled'),
    ]

    AUTH_TOKEN = 'token'

    AUTH_CHOICES = [
        (AUTH_TOKEN, 'Token'),
    ]

    name = models.CharField(max_length=255)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='integration_connections')
    connection_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_ERPNEXT)
    base_url = models.URLField()
    auth_type = models.CharField(max_length=16, choices=AUTH_CHOICES, default=AUTH_TOKEN)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    default_company = models.CharField(max_length=255, blank=True)
    default_warehouse = models.CharField(max_length=255, blank=True)
    poll_interval_minutes = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    last_failed_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self) -> str:
        return f'{self.name} ({self.connection_type})'


class IntegrationMapping(models.Model):
    ENTITY_PRODUCT = 'product'
    ENTITY_CATEGORY = 'category'
    ENTITY_WAREHOUSE = 'warehouse'
    ENTITY_CUSTOMER = 'customer'
    ENTITY_SUPPLIER = 'supplier'
    ENTITY_ORDER = 'order'
    ENTITY_PRICE = 'price'
    ENTITY_STOCK = 'stock'

    ENTITY_CHOICES = [
        (ENTITY_PRODUCT, 'Product'),
        (ENTITY_CATEGORY, 'Category'),
        (ENTITY_WAREHOUSE, 'Warehouse'),
        (ENTITY_CUSTOMER, 'Customer'),
        (ENTITY_SUPPLIER, 'Supplier'),
        (ENTITY_ORDER, 'Order'),
        (ENTITY_PRICE, 'Price'),
        (ENTITY_STOCK, 'Stock'),
    ]

    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, related_name='mappings')
    entity_type = models.CharField(max_length=32, choices=ENTITY_CHOICES)
    external_id = models.CharField(max_length=255)
    internal_model = models.CharField(max_length=120)
    internal_id = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['connection_id', 'entity_type', 'external_id']
        constraints = [
            models.UniqueConstraint(fields=['connection', 'entity_type', 'external_id'], name='uniq_integration_mapping_external'),
        ]

    def __str__(self) -> str:
        return f'{self.connection.name}::{self.entity_type}::{self.external_id}'


class SyncJob(models.Model):
    TYPE_PRODUCTS_IMPORT = 'products_import'
    TYPE_STOCK_IMPORT = 'stock_import'
    TYPE_PRICES_IMPORT = 'prices_import'
    TYPE_CUSTOMERS_IMPORT = 'customers_import'
    TYPE_SUPPLIERS_IMPORT = 'suppliers_import'
    TYPE_ORDERS_EXPORT = 'orders_export'
    TYPE_FULFILLMENT_IMPORT = 'fulfillment_import'
    TYPE_CONNECTION_TEST = 'connection_test'

    TYPE_CHOICES = [
        (TYPE_PRODUCTS_IMPORT, 'Products Import'),
        (TYPE_STOCK_IMPORT, 'Stock Import'),
        (TYPE_PRICES_IMPORT, 'Prices Import'),
        (TYPE_CUSTOMERS_IMPORT, 'Customers Import'),
        (TYPE_SUPPLIERS_IMPORT, 'Suppliers Import'),
        (TYPE_ORDERS_EXPORT, 'Orders Export'),
        (TYPE_FULFILLMENT_IMPORT, 'Fulfillment Import'),
        (TYPE_CONNECTION_TEST, 'Connection Test'),
    ]

    DIRECTION_INBOUND = 'inbound'
    DIRECTION_OUTBOUND = 'outbound'

    DIRECTION_CHOICES = [
        (DIRECTION_INBOUND, 'Inbound'),
        (DIRECTION_OUTBOUND, 'Outbound'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
    ]

    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, related_name='sync_jobs')
    job_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES, default=DIRECTION_INBOUND)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    cursor = models.CharField(max_length=255, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='integration_sync_jobs')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self) -> str:
        return f'{self.connection.name}::{self.job_type}::{self.status}'


class SyncEventLog(models.Model):
    STATUS_RECEIVED = 'received'
    STATUS_PROCESSED = 'processed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_RECEIVED, 'Received'),
        (STATUS_PROCESSED, 'Processed'),
        (STATUS_FAILED, 'Failed'),
    ]

    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, related_name='event_logs')
    job = models.ForeignKey(SyncJob, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_logs')
    direction = models.CharField(max_length=16, choices=SyncJob.DIRECTION_CHOICES, default=SyncJob.DIRECTION_INBOUND)
    entity_type = models.CharField(max_length=32, blank=True)
    external_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    payload_excerpt = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self) -> str:
        return f'{self.connection.name}::{self.entity_type or "event"}::{self.status}'
