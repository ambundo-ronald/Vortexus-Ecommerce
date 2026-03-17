from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255)),
                ('contact_name', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('country_code', models.CharField(blank=True, max_length=2)),
                ('website', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('suspended', 'Suspended')], default='pending', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('partner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_profile', to='partner.partner')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['company_name', 'id']},
        ),
    ]
