from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_producttaxconfiguration'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerprofile',
            name='bank_transfer_allowed',
            field=models.BooleanField(default=False),
        ),
    ]
