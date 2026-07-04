from celery import shared_task

from .services import cleanup_old_local_backups, create_backup, run_backup, verify_backup
from .models import BackupRun


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def run_backup_task(self, backup_run_id: int) -> int:
    run_backup(backup_run_id)
    cleanup_old_local_backups()
    return backup_run_id


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def create_scheduled_backup_task(self, backup_type: str = BackupRun.TYPE_FULL) -> int:
    run = create_backup(backup_type=backup_type)
    cleanup_old_local_backups()
    return run.id


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 2})
def verify_backup_task(self, backup_run_id: int) -> dict:
    run = BackupRun.objects.get(id=backup_run_id)
    return verify_backup(run)
