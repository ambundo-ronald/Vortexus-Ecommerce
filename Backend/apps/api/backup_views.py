from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.backups.models import BackupRun
from apps.backups.services import (
    BackupError,
    create_backup,
    latest_backup_status,
    serialize_backup_run,
    verify_backup,
)
from apps.backups.tasks import run_backup_task


class BackupTriggerSerializer(serializers.Serializer):
    backup_type = serializers.ChoiceField(
        choices=[BackupRun.TYPE_FULL, BackupRun.TYPE_DATABASE, BackupRun.TYPE_MEDIA],
        default=BackupRun.TYPE_FULL,
    )


def _require_superuser(request):
    return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class AdminBackupCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    throttle_scope = 'admin_backup'

    def get(self, request):
        page = max(int(request.query_params.get('page', 1) or 1), 1)
        page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
        queryset = BackupRun.objects.select_related('triggered_by').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        backup_type = request.query_params.get('backup_type')
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)
        total = queryset.count()
        start = (page - 1) * page_size
        rows = queryset[start : start + page_size]
        return Response(
            {
                'status': latest_backup_status(),
                'results': [serialize_backup_run(run) for run in rows],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'num_pages': (total + page_size - 1) // page_size if page_size else 1,
                    'has_next': start + page_size < total,
                },
            }
        )

    def post(self, request):
        if not _require_superuser(request):
            return Response({'detail': 'Only superusers can trigger backups.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BackupTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        backup_type = serializer.validated_data['backup_type']

        if getattr(settings, 'ENABLE_ASYNC_TASKS', False):
            run = BackupRun.objects.create(
                backup_type=backup_type,
                status=BackupRun.STATUS_PENDING,
                triggered_by=request.user,
                storage_backend=getattr(settings, 'BACKUP_STORAGE_BACKEND', 'local'),
                app_version=getattr(settings, 'APP_VERSION', ''),
            )
            run_backup_task.delay(run.id)
        else:
            run = create_backup(backup_type=backup_type, user=request.user)

        record_audit_event(
            event_type='backup.triggered',
            request=request,
            target=run,
            message=f'{backup_type} backup triggered.',
            metadata={'backup_type': backup_type, 'backup_id': run.id},
        )
        return Response({'backup': serialize_backup_run(run)}, status=status.HTTP_201_CREATED)


class AdminBackupDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, backup_id: int):
        run = BackupRun.objects.select_related('triggered_by').filter(id=backup_id).first()
        if not run:
            return Response({'detail': 'Backup not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'backup': serialize_backup_run(run)})


class AdminBackupVerifyAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    throttle_scope = 'admin_backup'

    def post(self, request, backup_id: int):
        run = BackupRun.objects.filter(id=backup_id).first()
        if not run:
            return Response({'detail': 'Backup not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = verify_backup(run)
        except BackupError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        record_audit_event(
            event_type='backup.verified',
            request=request,
            target=run,
            message='Backup checksum verified.' if result['valid'] else 'Backup checksum mismatch.',
            status='success' if result['valid'] else 'failure',
            metadata={'backup_id': run.id, 'valid': result['valid']},
        )
        return Response(result)


class AdminBackupDownloadAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    throttle_scope = 'admin_backup'

    def get(self, request, backup_id: int):
        if not _require_superuser(request):
            return Response({'detail': 'Only superusers can download backups.'}, status=status.HTTP_403_FORBIDDEN)
        run = BackupRun.objects.filter(id=backup_id, status=BackupRun.STATUS_SUCCESS).first()
        if not run:
            return Response({'detail': 'Successful backup not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = verify_backup(run)
        except BackupError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not result['valid']:
            return Response({'detail': 'Backup checksum verification failed.'}, status=status.HTTP_409_CONFLICT)

        path = Path(run.storage_path)
        record_audit_event(
            event_type='backup.downloaded',
            request=request,
            target=run,
            message='Backup downloaded.',
            metadata={'backup_id': run.id, 'size_bytes': run.size_bytes},
        )
        return FileResponse(path.open('rb'), as_attachment=True, filename=path.name)
