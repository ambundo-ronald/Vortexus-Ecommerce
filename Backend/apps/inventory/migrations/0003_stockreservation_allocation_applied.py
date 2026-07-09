from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_stockrecordpricesnapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockreservation',
            name='allocation_applied',
            field=models.BooleanField(default=True),
        ),
    ]
