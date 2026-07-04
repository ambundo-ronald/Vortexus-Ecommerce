from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0027_attributeoption_code_attributeoptiongroup_code_and_more'),
        ('accounts', '0011_deliveryroutecache'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductMongoReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_class', models.CharField(max_length=64)),
                ('mongo_id', models.CharField(db_index=True, max_length=64)),
                ('collection', models.CharField(blank=True, max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('last_synced_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'product',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='mongo_reference',
                        to='catalogue.product',
                    ),
                ),
            ],
            options={
                'ordering': ['product_id'],
                'indexes': [
                    models.Index(fields=['product_class'], name='accounts_pr_product_b17905_idx'),
                    models.Index(fields=['collection', 'mongo_id'], name='accounts_pr_collect_b4b762_idx'),
                ],
            },
        ),
    ]
