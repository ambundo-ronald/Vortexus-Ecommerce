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
            name='BackupRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backup_type', models.CharField(choices=[('full', 'Full'), ('database', 'Database'), ('media', 'Media')], default='full', max_length=16)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('storage_backend', models.CharField(default='local', max_length=32)),
                ('storage_path', models.CharField(blank=True, max_length=500)),
                ('manifest_path', models.CharField(blank=True, max_length=500)),
                ('checksum', models.CharField(blank=True, max_length=128)),
                ('size_bytes', models.BigIntegerField(default=0)),
                ('app_version', models.CharField(blank=True, max_length=80)),
                ('database_alias', models.CharField(default='default', max_length=80)),
                ('message', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('triggered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='triggered_backup_runs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='BackupRestoreRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('restore_mode', models.CharField(default='staging', max_length=32)),
                ('message', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('backup', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='restore_runs', to='backups.backuprun')),
                ('triggered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='triggered_restore_runs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='backuprun',
            index=models.Index(fields=['status', 'backup_type'], name='backups_bac_status_9d4f74_idx'),
        ),
        migrations.AddIndex(
            model_name='backuprun',
            index=models.Index(fields=['-created_at'], name='backups_bac_created_10ff95_idx'),
        ),
    ]
