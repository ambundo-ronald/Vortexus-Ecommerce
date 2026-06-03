from django.db import migrations, models


def protect_existing_passwords(apps, schema_editor):
    from apps.notifications.secret_store import is_sealed_secret, seal_secret

    EmailConfiguration = apps.get_model('notifications', 'EmailConfiguration')
    for config in EmailConfiguration.objects.exclude(password=''):
        if not is_sealed_secret(config.password):
            config.password = seal_secret(config.password)
            config.save(update_fields=['password'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_seed_security_communication_templates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailconfiguration',
            name='password',
            field=models.CharField(blank=True, max_length=1024),
        ),
        migrations.RunPython(protect_existing_passwords, noop),
    ]
