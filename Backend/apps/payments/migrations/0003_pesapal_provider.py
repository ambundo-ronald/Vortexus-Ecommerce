from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_paymentproviderconfiguration'),
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
                ],
                max_length=32,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='paymentsession',
            name='method',
            field=models.CharField(
                choices=[
                    ('mpesa', 'M-Pesa'),
                    ('pesapal', 'Pesapal'),
                    ('airtel_money', 'Airtel Money'),
                    ('credit_card', 'Credit Card'),
                    ('debit_card', 'Debit Card'),
                    ('bank_transfer', 'Bank Transfer'),
                    ('cash_on_delivery', 'Cash on Delivery'),
                ],
                max_length=32,
            ),
        ),
    ]
