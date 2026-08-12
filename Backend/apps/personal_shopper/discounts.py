import secrets
from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.utils import timezone


def _unique_code():
    Voucher = apps.get_model('voucher', 'Voucher')
    while True:
        code = f'HUB-{secrets.token_hex(4).upper()}'
        if not Voucher.objects.filter(code__iexact=code).exists():
            return code


def sync_shopper_discount(shopper_list):
    """Create or update the Oscar voucher offer backing a published shopper list."""
    Range = apps.get_model('offer', 'Range')
    Condition = apps.get_model('offer', 'Condition')
    Benefit = apps.get_model('offer', 'Benefit')
    Offer = apps.get_model('offer', 'ConditionalOffer')
    Voucher = apps.get_model('voucher', 'Voucher')
    percentage = Decimal(shopper_list.discount_percentage or 0)

    if percentage <= 0 or shopper_list.status in {'draft', 'archived'}:
        if shopper_list.discount_voucher_id:
            shopper_list.discount_voucher.offers.update(status=Offer.SUSPENDED)
        return None

    now = timezone.now()
    end = shopper_list.expires_at or (now + timedelta(days=30))
    voucher = shopper_list.discount_voucher
    if voucher is None:
        range_obj = Range.objects.create(
            name=f'Personal Shopper #{shopper_list.id}',
            description=f'Private product range for personal shopper list #{shopper_list.id}.',
            is_public=False,
        )
        condition = Condition.objects.create(range=range_obj, type=Condition.COUNT, value=1)
        benefit = Benefit.objects.create(range=range_obj, type=Benefit.PERCENTAGE, value=percentage)
        offer = Offer.objects.create(
            name=f'Personal Shopper #{shopper_list.id} discount',
            description=f'{percentage}% off curated Personal Shopper items.',
            offer_type=Offer.VOUCHER,
            status=Offer.OPEN,
            exclusive=True,
            condition=condition,
            benefit=benefit,
            start_datetime=now,
            end_datetime=end,
            max_global_applications=1,
            max_user_applications=1,
            max_basket_applications=1,
        )
        voucher = Voucher.objects.create(
            name=f'Personal Shopper #{shopper_list.id}',
            code=_unique_code(),
            usage=Voucher.SINGLE_USE,
            start_datetime=now,
            end_datetime=end,
        )
        voucher.offers.add(offer)
        shopper_list.discount_voucher = voucher
        shopper_list.save(update_fields=['discount_voucher', 'date_updated'])
    else:
        offer = voucher.offers.select_related('benefit', 'benefit__range').first()
        offer.status = Offer.OPEN
        offer.end_datetime = end
        offer.description = f'{percentage}% off curated Personal Shopper items.'
        offer.save(update_fields=['status', 'end_datetime', 'description'])
        offer.benefit.value = percentage
        offer.benefit.save(update_fields=['value'])
        voucher.end_datetime = end
        voucher.save(update_fields=['end_datetime'])
        range_obj = offer.benefit.range

    range_obj.included_products.set(shopper_list.items.values_list('product_id', flat=True))
    return voucher
