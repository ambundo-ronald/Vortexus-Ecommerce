from django.db import models


class StockReservation(models.Model):
    basket = models.ForeignKey('basket.Basket', on_delete=models.CASCADE, related_name='stock_reservations')
    line = models.OneToOneField('basket.Line', on_delete=models.CASCADE, related_name='stock_reservation')
    stockrecord = models.ForeignKey('partner.StockRecord', on_delete=models.CASCADE, related_name='basket_reservations')
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['basket_id', 'line_id']

    def __str__(self) -> str:
        return f'basket={self.basket_id} line={self.line_id} stockrecord={self.stockrecord_id} qty={self.quantity}'


class StockRecordPriceSnapshot(models.Model):
    stockrecord = models.OneToOneField('partner.StockRecord', on_delete=models.CASCADE, related_name='price_snapshot')
    previous_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    previous_currency = models.CharField(max_length=12, blank=True, default='')
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_currency = models.CharField(max_length=12, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['stockrecord_id']

    def __str__(self) -> str:
        return f'stockrecord={self.stockrecord_id} previous={self.previous_price} current={self.current_price}'
