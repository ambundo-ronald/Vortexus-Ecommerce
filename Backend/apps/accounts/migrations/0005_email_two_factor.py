from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0004_customerprofile_email_verified_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerprofile',
            name='two_factor_email_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='EmailTwoFactorChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_two_factor_challenges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', '-created_at'], name='accounts_em_user_id_811832_idx'),
                    models.Index(fields=['expires_at'], name='accounts_em_expires_c83671_idx'),
                ],
            },
        ),
    ]
