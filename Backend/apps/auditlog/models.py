from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILURE, 'Failure'),
    ]

    event_type = models.CharField(max_length=80, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events',
    )
    actor_email = models.EmailField(blank=True, default='', db_index=True)
    actor_role = models.CharField(max_length=40, blank=True, default='')
    request_method = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='', db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    target_type = models.CharField(max_length=120, blank=True, default='', db_index=True)
    target_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    target_repr = models.CharField(max_length=255, blank=True, default='')
    message = models.CharField(max_length=255, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        actor = self.actor_email or 'anonymous'
        return f'{self.event_type} ({self.status}) by {actor}'
