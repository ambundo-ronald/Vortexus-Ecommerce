from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(db_index=True, max_length=80)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failure', 'Failure')], db_index=True, default='success', max_length=20)),
                ('actor_email', models.EmailField(blank=True, db_index=True, default='', max_length=254)),
                ('actor_role', models.CharField(blank=True, default='', max_length=40)),
                ('request_method', models.CharField(blank=True, default='', max_length=10)),
                ('path', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, default='', max_length=255)),
                ('target_type', models.CharField(blank=True, db_index=True, default='', max_length=120)),
                ('target_id', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('target_repr', models.CharField(blank=True, default='', max_length=255)),
                ('message', models.CharField(blank=True, default='', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]
