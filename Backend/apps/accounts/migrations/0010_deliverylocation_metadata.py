from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_productattributemetadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverylocation',
            name='confidence',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='deliverylocation',
            name='formatted_address',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='deliverylocation',
            name='place_id',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='deliverylocation',
            name='provider',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
    ]
