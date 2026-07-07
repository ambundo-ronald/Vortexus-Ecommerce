from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from .models import BackupRun


BACKUP_EXCLUDED_APPS = {
    'admin.logentry',
    'contenttypes',
    'sessions.session',
}


class BackupError(Exception):
    pass


def backup_root() -> Path:
    root = Path(getattr(settings, 'BACKUP_ROOT', settings.BASE_DIR / 'backups'))
    root.mkdir(parents=True, exist_ok=True)
    return root


def serialize_backup_run(run: BackupRun) -> dict:
    return {
        'id': run.id,
        'backup_type': run.backup_type,
        'status': run.status,
        'storage_backend': run.storage_backend,
        'storage_path': run.storage_path,
        'manifest_path': run.manifest_path,
        'checksum': run.checksum,
        'size_bytes': run.size_bytes,
        'size_mb': round((run.size_bytes or 0) / (1024 * 1024), 2),
        'app_version': run.app_version,
        'database_alias': run.database_alias,
        'message': run.message,
        'metadata': run.metadata or {},
        'triggered_by': getattr(run.triggered_by, 'email', '') or getattr(run.triggered_by, 'username', '') if run.triggered_by_id else '',
        'started_at': run.started_at.isoformat() if run.started_at else None,
        'finished_at': run.finished_at.isoformat() if run.finished_at else None,
        'created_at': run.created_at.isoformat() if run.created_at else None,
        'updated_at': run.updated_at.isoformat() if run.updated_at else None,
    }


def latest_backup_status() -> dict:
    latest = BackupRun.objects.order_by('-created_at').first()
    latest_success = BackupRun.objects.filter(status=BackupRun.STATUS_SUCCESS).order_by('-finished_at', '-created_at').first()
    latest_failed = BackupRun.objects.filter(status=BackupRun.STATUS_FAILED).order_by('-finished_at', '-created_at').first()
    return {
        'latest': serialize_backup_run(latest) if latest else None,
        'latest_success': serialize_backup_run(latest_success) if latest_success else None,
        'latest_failed': serialize_backup_run(latest_failed) if latest_failed else None,
        'success_count': BackupRun.objects.filter(status=BackupRun.STATUS_SUCCESS).count(),
        'failed_count': BackupRun.objects.filter(status=BackupRun.STATUS_FAILED).count(),
        'running_count': BackupRun.objects.filter(status__in=[BackupRun.STATUS_PENDING, BackupRun.STATUS_RUNNING]).count(),
        'storage_backend': getattr(settings, 'BACKUP_STORAGE_BACKEND', 'local'),
        'backup_root': str(backup_root()),
    }


def create_backup(*, backup_type: str = BackupRun.TYPE_FULL, user=None) -> BackupRun:
    run = BackupRun.objects.create(
        backup_type=backup_type,
        status=BackupRun.STATUS_PENDING,
        triggered_by=user if getattr(user, 'is_authenticated', False) else None,
        storage_backend=getattr(settings, 'BACKUP_STORAGE_BACKEND', 'local'),
        app_version=getattr(settings, 'APP_VERSION', ''),
    )
    return run_backup(run.id)


def run_backup(run_id: int) -> BackupRun:
    run = BackupRun.objects.get(id=run_id)
    run.status = BackupRun.STATUS_RUNNING
    run.started_at = timezone.now()
    run.message = ''
    run.save(update_fields=['status', 'started_at', 'message', 'updated_at'])

    try:
        if run.backup_type not in {BackupRun.TYPE_FULL, BackupRun.TYPE_DATABASE, BackupRun.TYPE_MEDIA}:
            raise BackupError('Unsupported backup type.')

        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        bundle_name = f'vortexus-{run.backup_type}-{timestamp}-{run.id}.zip'
        destination = backup_root() / bundle_name

        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = build_backup_payload(run, tmp_path)
            manifest_path = tmp_path / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')

            with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for file_path in tmp_path.rglob('*'):
                    if file_path.is_file():
                        archive.write(file_path, file_path.relative_to(tmp_path).as_posix())

        checksum = file_sha256(destination)
        size_bytes = destination.stat().st_size
        manifest_destination = destination.with_suffix('.manifest.json')
        manifest_destination.write_text(
            json.dumps(
                {
                    **manifest,
                    'bundle': destination.name,
                    'checksum_sha256': checksum,
                    'size_bytes': size_bytes,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding='utf-8',
        )

        run.status = BackupRun.STATUS_SUCCESS
        run.finished_at = timezone.now()
        run.storage_path = str(destination)
        run.manifest_path = str(manifest_destination)
        run.checksum = checksum
        run.size_bytes = size_bytes
        run.message = 'Backup completed successfully.'
        run.metadata = {'bundle': destination.name}
        run.save()
        return run
    except Exception as exc:
        run.status = BackupRun.STATUS_FAILED
        run.finished_at = timezone.now()
        run.message = str(exc)
        run.save(update_fields=['status', 'finished_at', 'message', 'updated_at'])
        raise


def build_backup_payload(run: BackupRun, tmp_path: Path) -> dict:
    files: list[dict] = []
    if run.backup_type in {BackupRun.TYPE_FULL, BackupRun.TYPE_DATABASE}:
        database_path = tmp_path / 'database.json'
        dump_database(database_path)
        files.append(file_metadata(database_path, 'database'))

    if run.backup_type in {BackupRun.TYPE_FULL, BackupRun.TYPE_MEDIA}:
        media_path = tmp_path / 'media.zip'
        archive_media(media_path)
        files.append(file_metadata(media_path, 'media'))

    return {
        'backup_id': run.id,
        'backup_type': run.backup_type,
        'created_at': timezone.now().isoformat(),
        'database_alias': run.database_alias,
        'storage_backend': run.storage_backend,
        'media_root': str(settings.MEDIA_ROOT),
        'files': files,
        'restore_notes': [
            'Restore database.json with Django loaddata in a clean/staging environment first.',
            'Extract media.zip into MEDIA_ROOT after verifying the checksum.',
            'Run migrations and rebuild OpenSearch indexes after restore.',
            'Reconcile payment provider and ERPNext records before resuming fulfillment.',
        ],
    }


def dump_database(destination: Path) -> None:
    args = [
        '--natural-foreign',
        '--natural-primary',
        '--indent',
        '2',
        *[f'--exclude={label}' for label in sorted(BACKUP_EXCLUDED_APPS)],
    ]
    with destination.open('w', encoding='utf-8') as output:
        call_command(
            'dumpdata',
            *args,
            stdout=output,
        )


def archive_media(destination: Path) -> None:
    media_root = Path(settings.MEDIA_ROOT)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        if not media_root.exists():
            return
        for file_path in media_root.rglob('*'):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(media_root).as_posix())


def verify_backup(run: BackupRun) -> dict:
    if not run.storage_path:
        raise BackupError('Backup does not have a storage path.')
    path = Path(run.storage_path)
    if not path.exists():
        raise BackupError('Backup file is missing from storage.')
    checksum = file_sha256(path)
    valid = checksum == run.checksum
    return {
        'valid': valid,
        'expected_checksum': run.checksum,
        'actual_checksum': checksum,
        'size_bytes': path.stat().st_size,
    }


def cleanup_old_local_backups(*, keep: int | None = None) -> int:
    keep = keep or int(getattr(settings, 'BACKUP_LOCAL_KEEP', 30))
    successful = list(BackupRun.objects.filter(status=BackupRun.STATUS_SUCCESS).order_by('-created_at'))
    deleted = 0
    for run in successful[keep:]:
        for path_value in [run.storage_path, run.manifest_path]:
            if not path_value:
                continue
            path = Path(path_value)
            if path.exists() and path.is_file():
                path.unlink()
                deleted += 1
    return deleted


def file_metadata(path: Path, kind: str) -> dict:
    return {
        'kind': kind,
        'name': path.name,
        'size_bytes': path.stat().st_size,
        'checksum_sha256': file_sha256(path),
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def restore_backup_to_directory(run: BackupRun, destination: Path) -> dict:
    if run.status != BackupRun.STATUS_SUCCESS:
        raise BackupError('Only successful backups can be restored.')
    verification = verify_backup(run)
    if not verification['valid']:
        raise BackupError('Backup checksum verification failed.')
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(run.storage_path, 'r') as archive:
        archive.extractall(destination)
    return {
        'destination': str(destination),
        'files': sorted(os.listdir(destination)),
    }


def copy_backup_to_download_path(run: BackupRun, destination: Path) -> Path:
    verification = verify_backup(run)
    if not verification['valid']:
        raise BackupError('Backup checksum verification failed.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(run.storage_path, destination)
    return destination
