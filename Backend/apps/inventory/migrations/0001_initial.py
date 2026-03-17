from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('basket', '0012_line_code'),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('basket', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='stock_reservations', to='basket.basket')),
                ('line', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='stock_reservation', to='basket.line')),
                ('stockrecord', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='basket_reservations', to='partner.stockrecord')),
            ],
            options={'ordering': ['basket_id', 'line_id']},
        ),
    ]
