from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0001_initial'),
        ('order', '0018_alter_line_num_allocated'),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierOrderGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('packed', 'Packed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('partially_shipped', 'Partially Shipped')], default='pending', max_length=32)),
                ('line_count', models.PositiveIntegerField(default=0)),
                ('item_count', models.PositiveIntegerField(default=0)),
                ('total_excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('shipping_excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('shipping_incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('tracking_reference', models.CharField(blank=True, max_length=128)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_groups', to='order.order')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_groups', to='partner.partner')),
            ],
            options={'ordering': ['order_id', 'partner_id']},
        ),
        migrations.AddConstraint(
            model_name='supplierordergroup',
            constraint=models.UniqueConstraint(fields=('order', 'partner'), name='uniq_supplier_group_order_partner'),
        ),
    ]
