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
    provider = models.CharField(max_length=32, blank=True, default='')
    place_id = models.CharField(max_length=128, blank=True, default='')
    formatted_address = models.CharField(max_length=255, blank=True, default='')
    confidence = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
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


class DistanceDeliveryMethod(models.Model):
    VEHICLE_MOTORCYCLE = 'motorcycle'
    VEHICLE_VAN = 'van'
    VEHICLE_TRUCK = 'truck'

    VEHICLE_CHOICES = [
        (VEHICLE_MOTORCYCLE, 'Motorcycle'),
        (VEHICLE_VAN, 'Van'),
        (VEHICLE_TRUCK, 'Truck'),
    ]

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    vehicle_type = models.CharField(max_length=32, choices=VEHICLE_CHOICES, default=VEHICLE_MOTORCYCLE)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rate_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_distance_km = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    maximum_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    origin_label = models.CharField(max_length=120, blank=True)
    origin_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    origin_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['vehicle_type', 'is_active']),
        ]

    def __str__(self):
        return self.name


class DeliveryRouteCache(models.Model):
    provider = models.CharField(max_length=32, default='straight_line')
    vehicle_type = models.CharField(max_length=32, default='driving')
    origin_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    origin_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    duration_seconds = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=32, blank=True, default='')
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'provider',
                    'vehicle_type',
                    'origin_latitude',
                    'origin_longitude',
                    'destination_latitude',
                    'destination_longitude',
                ],
                name='accounts_delivery_route_cache_unique',
            ),
        ]
        indexes = [
            models.Index(fields=['provider', 'vehicle_type']),
            models.Index(fields=['origin_latitude', 'origin_longitude']),
            models.Index(fields=['destination_latitude', 'destination_longitude']),
        ]

    def __str__(self):
        return f'{self.provider}:{self.vehicle_type}:{self.distance_km}km'


class ProductAttributeMetadata(models.Model):
    DATA_TYPE_UOM = 'uom'

    attribute = models.OneToOneField(
        'catalogue.ProductAttribute',
        on_delete=models.CASCADE,
        related_name='vortexus_metadata',
    )
    parent_attribute = models.ForeignKey(
        'catalogue.ProductAttribute',
        on_delete=models.SET_NULL,
        related_name='vortexus_child_metadata',
        blank=True,
        null=True,
    )
    data_type = models.CharField(max_length=32, blank=True)
    uom = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['attribute__code']
        indexes = [
            models.Index(fields=['data_type']),
            models.Index(fields=['uom']),
        ]

    def __str__(self):
        return f'ProductAttributeMetadata(attribute_id={self.attribute_id})'
