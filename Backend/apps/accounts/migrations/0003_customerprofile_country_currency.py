from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_seed_shipping_countries'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerprofile',
            name='country_code',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='preferred_currency',
            field=models.CharField(blank=True, max_length=3),
        ),
    ]
