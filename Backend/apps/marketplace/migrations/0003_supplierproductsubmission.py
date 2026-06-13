from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogue', '0027_attributeoption_code_attributeoptiongroup_code_and_more'),
        ('marketplace', '0002_supplierordergroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierProductSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('draft', 'Draft'),
                            ('pending_review', 'Pending Review'),
                            ('changes_requested', 'Changes Requested'),
                            ('approved', 'Approved'),
                            ('rejected', 'Rejected'),
                            ('suspended', 'Suspended'),
                        ],
                        default='pending_review',
                        max_length=32,
                    ),
                ),
                ('supplier_note', models.TextField(blank=True)),
                ('review_note', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'product',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='supplier_submission',
                        to='catalogue.product',
                    ),
                ),
                (
                    'reviewed_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='reviewed_supplier_product_submissions',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'submitted_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='supplier_product_submissions',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'supplier',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='product_submissions',
                        to='marketplace.supplierprofile',
                    ),
                ),
            ],
            options={
                'ordering': ['-updated_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='supplierproductsubmission',
            index=models.Index(fields=['status', 'updated_at'], name='marketplace_status_645f68_idx'),
        ),
        migrations.AddIndex(
            model_name='supplierproductsubmission',
            index=models.Index(fields=['supplier', 'status'], name='marketplace_supplie_769ff3_idx'),
        ),
    ]
