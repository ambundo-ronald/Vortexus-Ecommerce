from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0006_auto_20181115_1953'),
        ('accounts', '0006_rename_accounts_em_user_id_811832_idx_accounts_em_user_id_fbe98a_idx_and_more'),
        ('order', '0018_alter_line_num_allocated'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('label', models.CharField(blank=True, max_length=120)),
                ('source', models.CharField(blank=True, max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'shipping_address',
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='delivery_location',
                        to='order.shippingaddress',
                    ),
                ),
                (
                    'user_address',
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='delivery_location',
                        to='address.useraddress',
                    ),
                ),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='deliverylocation',
            index=models.Index(fields=['latitude', 'longitude'], name='accounts_de_latitud_312f7e_idx'),
        ),
    ]
