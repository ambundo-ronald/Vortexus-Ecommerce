from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('marketplace', '0003_supplierproductsubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierprofile',
            name='account_manager',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='managed_supplier_profiles',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='supplierprofile',
            name='status_note',
            field=models.TextField(blank=True),
        ),
    ]
