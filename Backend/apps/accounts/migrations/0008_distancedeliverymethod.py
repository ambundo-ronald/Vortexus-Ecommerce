from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_deliverylocation'),
    ]

    operations = [
        migrations.CreateModel(
            name='DistanceDeliveryMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=80, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('vehicle_type', models.CharField(choices=[('motorcycle', 'Motorcycle'), ('van', 'Van'), ('truck', 'Truck')], default='motorcycle', max_length=32)),
                ('base_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('rate_per_km', models.DecimalField(decimal_places=2, max_digits=10)),
                ('minimum_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('maximum_distance_km', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('maximum_weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('origin_label', models.CharField(blank=True, max_length=120)),
                ('origin_latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('origin_longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sort_order', 'name'],
                'indexes': [models.Index(fields=['is_active', 'sort_order'], name='accounts_di_is_acti_8686c0_idx'), models.Index(fields=['vehicle_type', 'is_active'], name='accounts_di_vehicle_849c83_idx')],
            },
        ),
    ]
