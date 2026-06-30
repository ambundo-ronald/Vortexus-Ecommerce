from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0027_attributeoption_code_attributeoptiongroup_code_and_more'),
        ('accounts', '0008_distancedeliverymethod'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductAttributeMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_type', models.CharField(blank=True, max_length=32)),
                ('uom', models.CharField(blank=True, max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'attribute',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='vortexus_metadata',
                        to='catalogue.productattribute',
                    ),
                ),
                (
                    'parent_attribute',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='vortexus_child_metadata',
                        to='catalogue.productattribute',
                    ),
                ),
            ],
            options={
                'ordering': ['attribute__code'],
            },
        ),
        migrations.AddIndex(
            model_name='productattributemetadata',
            index=models.Index(fields=['data_type'], name='accounts_pr_data_t_62e25c_idx'),
        ),
        migrations.AddIndex(
            model_name='productattributemetadata',
            index=models.Index(fields=['uom'], name='accounts_pr_uom_0c5f4a_idx'),
        ),
    ]
