from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_customerprofile_country_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerprofile',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
