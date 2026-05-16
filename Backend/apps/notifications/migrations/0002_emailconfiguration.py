from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('smtp', 'SMTP')], default='smtp', max_length=32, unique=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('host', models.CharField(blank=True, max_length=255)),
                ('port', models.PositiveIntegerField(default=587)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('password', models.CharField(blank=True, max_length=255)),
                ('use_tls', models.BooleanField(default=True)),
                ('use_ssl', models.BooleanField(default=False)),
                ('timeout_seconds', models.PositiveIntegerField(default=30)),
                ('from_email', models.EmailField(blank=True, max_length=254)),
                ('reply_to_email', models.EmailField(blank=True, max_length=254)),
                ('sales_recipients', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_configuration_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['provider'],
            },
        ),
    ]
