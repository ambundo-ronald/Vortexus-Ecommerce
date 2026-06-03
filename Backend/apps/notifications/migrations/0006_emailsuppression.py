from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0005_protect_email_configuration_password'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSuppression',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('reason', models.CharField(choices=[('bounce', 'Bounce'), ('complaint', 'Complaint'), ('manual', 'Manual'), ('unsubscribe', 'Unsubscribe')], default='manual', max_length=32)),
                ('source', models.CharField(blank=True, max_length=64)),
                ('note', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_suppressions_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['email'],
            },
        ),
    ]
