from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_deliverylocation_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryRouteCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(default='straight_line', max_length=32)),
                ('vehicle_type', models.CharField(default='driving', max_length=32)),
                ('origin_latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('origin_longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('destination_latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('destination_longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('distance_km', models.DecimalField(decimal_places=2, max_digits=10)),
                ('duration_seconds', models.PositiveIntegerField(default=0)),
                ('source', models.CharField(blank=True, default='', max_length=32)),
                ('raw_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [
                    models.Index(fields=['provider', 'vehicle_type'], name='accounts_de_provide_166fb8_idx'),
                    models.Index(fields=['origin_latitude', 'origin_longitude'], name='accounts_de_origin__229cb6_idx'),
                    models.Index(fields=['destination_latitude', 'destination_longitude'], name='accounts_de_destina_67a1ca_idx'),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('provider', 'vehicle_type', 'origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude'),
                        name='accounts_delivery_route_cache_unique',
                    ),
                ],
            },
        ),
    ]
