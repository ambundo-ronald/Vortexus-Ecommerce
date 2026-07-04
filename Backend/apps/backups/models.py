from django.conf import settings
from django.db import models


class BackupRun(models.Model):
    TYPE_FULL = 'full'
    TYPE_DATABASE = 'database'
    TYPE_MEDIA = 'media'
    TYPE_CHOICES = (
        (TYPE_FULL, 'Full'),
        (TYPE_DATABASE, 'Database'),
        (TYPE_MEDIA, 'Media'),
    )

    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    )

    backup_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_FULL)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='triggered_backup_runs',
    )
    storage_backend = models.CharField(max_length=32, default='local')
    storage_path = models.CharField(max_length=500, blank=True)
    manifest_path = models.CharField(max_length=500, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    app_version = models.CharField(max_length=80, blank=True)
    database_alias = models.CharField(max_length=80, default='default')
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('status', 'backup_type'), name='backups_bac_status_9d4f74_idx'),
            models.Index(fields=('-created_at',), name='backups_bac_created_10ff95_idx'),
        ]

    def __str__(self):
        return f'{self.get_backup_type_display()} backup #{self.pk} ({self.status})'


class BackupRestoreRun(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    )

    backup = models.ForeignKey(BackupRun, on_delete=models.PROTECT, related_name='restore_runs')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    restore_mode = models.CharField(max_length=32, default='staging')
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='triggered_restore_runs',
    )
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Restore #{self.pk} from backup #{self.backup_id} ({self.status})'
