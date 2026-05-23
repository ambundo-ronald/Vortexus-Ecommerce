from django.apps import apps
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

StockRecord = apps.get_model('partner', 'StockRecord')


@receiver(pre_save, sender=StockRecord)
def remember_previous_stockrecord_price(sender, instance, **kwargs):
    if not instance.pk:
        instance._vortexus_previous_price = None
        return

    previous = sender.objects.filter(pk=instance.pk).only('price', 'price_currency').first()
    if previous is None:
        instance._vortexus_previous_price = None
        return

    previous_price = getattr(previous, 'price', None)
    previous_currency = getattr(previous, 'price_currency', None) or ''
    current_price = getattr(instance, 'price', None)
    current_currency = getattr(instance, 'price_currency', None) or ''

    if previous_price == current_price and previous_currency == current_currency:
        instance._vortexus_previous_price = None
        return

    instance._vortexus_previous_price = (previous_price, previous_currency)


@receiver(post_save, sender=StockRecord)
def persist_stockrecord_price_snapshot(sender, instance, created, **kwargs):
    PriceSnapshot = apps.get_model('inventory', 'StockRecordPriceSnapshot')
    current_price = getattr(instance, 'price', None)
    current_currency = getattr(instance, 'price_currency', None) or ''

    if current_price is None:
        return

    previous = getattr(instance, '_vortexus_previous_price', None)
    if not previous:
        PriceSnapshot.objects.update_or_create(
            stockrecord=instance,
            defaults={
                'current_price': current_price,
                'current_currency': current_currency,
            },
        )
        return

    previous_price, previous_currency = previous
    if previous_price is None:
        return

    PriceSnapshot.objects.update_or_create(
        stockrecord=instance,
        defaults={
            'previous_price': previous_price,
            'previous_currency': previous_currency or current_currency,
            'current_price': current_price,
            'current_currency': current_currency,
        },
    )
