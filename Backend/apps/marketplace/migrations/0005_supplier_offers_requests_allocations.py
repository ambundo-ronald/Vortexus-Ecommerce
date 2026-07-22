import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogue', '0027_attributeoption_code_attributeoptiongroup_code_and_more'),
        ('marketplace', '0004_supplierprofile_account_manager_and_status_note'),
        ('order', '0018_alter_line_num_allocated'),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierProductOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supplier_sku', models.CharField(blank=True, max_length=128)),
                ('supplier_unit_cost', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(default='KES', max_length=12)),
                ('available_quantity', models.PositiveIntegerField(default=0)),
                ('lead_time_days', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('review_note', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending_review', 'Pending Review'), ('approved', 'Approved'), ('changes_requested', 'Changes Requested'), ('rejected', 'Rejected'), ('suspended', 'Suspended')], default='pending_review', max_length=32)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_offers', to='catalogue.product')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_supplier_offers', to=settings.AUTH_USER_MODEL)),
                ('stockrecord', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_offer', to='partner.stockrecord')),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_supplier_offers', to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_offers', to='marketplace.supplierprofile')),
            ],
            options={
                'ordering': ['-updated_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='SupplierProductRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_title', models.CharField(max_length=255)),
                ('brand', models.CharField(blank=True, max_length=128)),
                ('category_hint', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('specs', models.JSONField(blank=True, default=dict)),
                ('supplier_sku', models.CharField(blank=True, max_length=128)),
                ('supplier_unit_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(default='KES', max_length=12)),
                ('available_quantity', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('review_note', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending_review', 'Pending Review'), ('approved', 'Approved'), ('changes_requested', 'Changes Requested'), ('rejected', 'Rejected')], default='pending_review', max_length=32)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('linked_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_requests', to='catalogue.product')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_supplier_product_requests', to=settings.AUTH_USER_MODEL)),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_supplier_product_requests', to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_requests', to='marketplace.supplierprofile')),
            ],
            options={
                'ordering': ['-updated_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='SupplierOrderLineAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('customer_unit_price_excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('customer_unit_price_incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('supplier_unit_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('supplier_total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('gross_margin', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('currency', models.CharField(default='KES', max_length=12)),
                ('payout_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='pending', max_length=32)),
                ('payout_reference', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_allocations', to='order.line')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_allocations', to='order.order')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_line_allocations', to='partner.partner')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_order_allocations', to='catalogue.product')),
                ('stockrecord', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_line_allocations', to='partner.stockrecord')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_line_allocations', to='marketplace.supplierprofile')),
                ('supplier_offer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_line_allocations', to='marketplace.supplierproductoffer')),
            ],
            options={
                'ordering': ['order_id', 'line_id', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='supplierproductoffer',
            constraint=models.UniqueConstraint(fields=('supplier', 'product'), name='uniq_supplier_offer_supplier_product'),
        ),
        migrations.AddIndex(
            model_name='supplierproductoffer',
            index=models.Index(fields=['supplier', 'status'], name='supp_offer_supplier_status'),
        ),
        migrations.AddIndex(
            model_name='supplierproductoffer',
            index=models.Index(fields=['product', 'status'], name='supp_offer_product_status'),
        ),
        migrations.AddIndex(
            model_name='supplierproductoffer',
            index=models.Index(fields=['status', 'updated_at'], name='supp_offer_status_updated'),
        ),
        migrations.AddIndex(
            model_name='supplierproductrequest',
            index=models.Index(fields=['supplier', 'status'], name='supp_req_supplier_status'),
        ),
        migrations.AddIndex(
            model_name='supplierproductrequest',
            index=models.Index(fields=['status', 'updated_at'], name='supp_req_status_updated'),
        ),
        migrations.AddIndex(
            model_name='supplierorderlineallocation',
            index=models.Index(fields=['partner', 'payout_status'], name='supp_alloc_partner_payout'),
        ),
        migrations.AddIndex(
            model_name='supplierorderlineallocation',
            index=models.Index(fields=['supplier', 'payout_status'], name='supp_alloc_supplier_payout'),
        ),
        migrations.AddIndex(
            model_name='supplierorderlineallocation',
            index=models.Index(fields=['order', 'partner'], name='supp_alloc_order_partner'),
        ),
    ]
