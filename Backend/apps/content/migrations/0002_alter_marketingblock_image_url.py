from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketingblock',
            name='image_url',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
