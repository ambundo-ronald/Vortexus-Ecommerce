from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockRecordPriceSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('previous_currency', models.CharField(blank=True, default='', max_length=12)),
                ('current_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('current_currency', models.CharField(blank=True, default='', max_length=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'stockrecord',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='price_snapshot',
                        to='partner.stockrecord',
                    ),
                ),
            ],
            options={'ordering': ['stockrecord_id']},
        ),
    ]
