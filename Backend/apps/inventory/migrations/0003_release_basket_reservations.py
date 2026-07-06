from django.db import migrations


def release_basket_reservations(apps, schema_editor):
    StockReservation = apps.get_model('inventory', 'StockReservation')
    StockRecord = apps.get_model('partner', 'StockRecord')

    reservations = list(StockReservation.objects.values('stockrecord_id', 'quantity'))
    if not reservations:
        return

    by_stockrecord = {}
    for reservation in reservations:
        stockrecord_id = reservation.get('stockrecord_id')
        if not stockrecord_id:
            continue
        by_stockrecord[stockrecord_id] = by_stockrecord.get(stockrecord_id, 0) + int(reservation.get('quantity') or 0)

    for stockrecord_id, quantity in by_stockrecord.items():
        if quantity <= 0:
            continue
        stockrecord = StockRecord.objects.filter(id=stockrecord_id).first()
        if not stockrecord:
            continue
        allocated = int(stockrecord.num_allocated or 0)
        stockrecord.num_allocated = max(allocated - quantity, 0)
        stockrecord.save(update_fields=['num_allocated'])

    StockReservation.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0002_stockrecordpricesnapshot'),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.RunPython(release_basket_reservations, migrations.RunPython.noop),
    ]
