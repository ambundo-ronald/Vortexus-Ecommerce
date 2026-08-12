from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('personal_shopper', '0001_initial'),
        ('voucher', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='shopperlist',
            name='discount_percentage',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
        migrations.AddField(
            model_name='shopperlist',
            name='discount_voucher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personal_shopper_lists', to='voucher.voucher'),
        ),
    ]
