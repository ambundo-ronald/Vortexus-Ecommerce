from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_alter_paymentproviderconfiguration_provider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentproviderconfiguration',
            name='provider',
            field=models.CharField(
                choices=[
                    ('mpesa', 'M-Pesa'),
                    ('pesapal', 'Pesapal'),
                    ('airtel_money', 'Airtel Money'),
                    ('card', 'Card'),
                    ('bank_transfer', 'Bank Transfer'),
                    ('cash_on_delivery', 'Cash on Delivery'),
                ],
                max_length=32,
                unique=True,
            ),
        ),
    ]
