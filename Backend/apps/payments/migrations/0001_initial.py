from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('basket', '0012_line_code'),
        ('order', '0018_alter_line_num_allocated'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(choices=[('mpesa', 'M-Pesa'), ('airtel_money', 'Airtel Money'), ('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('bank_transfer', 'Bank Transfer'), ('cash_on_delivery', 'Cash on Delivery')], max_length=32)),
                ('status', models.CharField(choices=[('initialized', 'Initialized'), ('pending', 'Pending'), ('authorized', 'Authorized'), ('paid', 'Paid'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='initialized', max_length=16)),
                ('provider', models.CharField(max_length=64)),
                ('reference', models.CharField(max_length=64, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(max_length=12)),
                ('payer_email', models.EmailField(blank=True, max_length=254)),
                ('payer_phone', models.CharField(blank=True, max_length=40)),
                ('external_reference', models.CharField(blank=True, max_length=128)),
                ('provider_payload', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('basket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_sessions', to='basket.basket')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_sessions', to='order.order')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
