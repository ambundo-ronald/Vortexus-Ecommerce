from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentProviderConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('mpesa', 'M-Pesa'), ('airtel_money', 'Airtel Money'), ('card', 'Card')], max_length=32, unique=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('public_config', models.JSONField(blank=True, default=dict)),
                ('secret_config', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_provider_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['provider'],
            },
        ),
    ]
