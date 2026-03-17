from django.conf import settings
from django.db import models


class PaymentSession(models.Model):
    METHOD_MPESA = 'mpesa'
    METHOD_AIRTEL_MONEY = 'airtel_money'
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD = 'debit_card'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_CASH_ON_DELIVERY = 'cash_on_delivery'

    METHOD_CHOICES = [
        (METHOD_MPESA, 'M-Pesa'),
        (METHOD_AIRTEL_MONEY, 'Airtel Money'),
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_DEBIT_CARD, 'Debit Card'),
        (METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (METHOD_CASH_ON_DELIVERY, 'Cash on Delivery'),
    ]

    STATUS_INITIALIZED = 'initialized'
    STATUS_PENDING = 'pending'
    STATUS_AUTHORIZED = 'authorized'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_INITIALIZED, 'Initialized'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_AUTHORIZED, 'Authorized'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    basket = models.ForeignKey('basket.Basket', null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    order = models.ForeignKey('order.Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_sessions')
    method = models.CharField(max_length=32, choices=METHOD_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_INITIALIZED)
    provider = models.CharField(max_length=64)
    reference = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12)
    payer_email = models.EmailField(blank=True)
    payer_phone = models.CharField(max_length=40, blank=True)
    external_reference = models.CharField(max_length=128, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.reference}:{self.method}:{self.status}'

