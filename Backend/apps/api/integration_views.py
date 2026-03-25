from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.integrations.erpnext_sync import ERPNextSyncService
from apps.integrations.models import IntegrationConnection, SyncEventLog, SyncJob
from apps.integrations.services import ERPNextIntegrationError, build_erpnext_client

from .integration_serializers import (
    ERPNextImportRequestSerializer,
    IntegrationConnectionSerializer,
    IntegrationPreviewQuerySerializer,
    SyncEventLogSerializer,
)


class IntegrationConnectionCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = IntegrationConnection.objects.select_related('partner').order_by('name', 'id')
        return Response({'results': IntegrationConnectionSerializer(queryset, many=True).data})

    @transaction.atomic
    def post(self, request):
        serializer = IntegrationConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        connection = serializer.save()
        record_audit_event(
            event_type='integrations.connection_created',
            request=request,
            actor=request.user,
            target=connection,
            message='Integration connection created.',
            metadata={'connection_type': connection.connection_type, 'base_url': connection.base_url},
        )
        return Response({'connection': IntegrationConnectionSerializer(connection).data}, status=status.HTTP_201_CREATED)


class IntegrationConnectionDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection.objects.select_related('partner'), id=connection_id)
        return Response({'connection': IntegrationConnectionSerializer(connection).data})

    @transaction.atomic
    def patch(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id)
        serializer = IntegrationConnectionSerializer(connection, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        connection = serializer.save()
        record_audit_event(
            event_type='integrations.connection_updated',
            request=request,
            actor=request.user,
            target=connection,
            message='Integration connection updated.',
            metadata={'connection_type': connection.connection_type, 'base_url': connection.base_url, 'status': connection.status},
        )
        return Response({'connection': IntegrationConnectionSerializer(connection).data})


class IntegrationLogCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id)
        queryset = connection.event_logs.order_by('-created_at', '-id')[:100]
        return Response({'results': SyncEventLogSerializer(queryset, many=True).data})


class ERPNextConnectionTestAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
        job = SyncJob.objects.create(
            connection=connection,
            job_type=SyncJob.TYPE_CONNECTION_TEST,
            direction=SyncJob.DIRECTION_INBOUND,
            status=SyncJob.STATUS_RUNNING,
            created_by=request.user,
            started_at=timezone.now(),
        )
        try:
            result = build_erpnext_client(connection).test_connection()
        except ERPNextIntegrationError as exc:
            connection.status = IntegrationConnection.STATUS_ERROR
            connection.last_failed_sync_at = timezone.now()
            connection.save(update_fields=['status', 'last_failed_sync_at', 'updated_at'])
            job.status = SyncJob.STATUS_FAILED
            job.error_message = str(exc)
            job.finished_at = timezone.now()
            job.summary = {'ok': False}
            job.save(update_fields=['status', 'error_message', 'finished_at', 'summary'])
            SyncEventLog.objects.create(
                connection=connection,
                job=job,
                direction=SyncJob.DIRECTION_INBOUND,
                entity_type='connection_test',
                status=SyncEventLog.STATUS_FAILED,
                error_message=str(exc),
                payload_excerpt={'base_url': connection.base_url},
            )
            raise serializers.ValidationError({'connection': str(exc)}) from exc

        connection.status = IntegrationConnection.STATUS_ACTIVE
        connection.last_successful_sync_at = timezone.now()
        connection.save(update_fields=['status', 'last_successful_sync_at', 'updated_at'])
        job.status = SyncJob.STATUS_SUCCEEDED
        job.finished_at = timezone.now()
        job.summary = result
        job.save(update_fields=['status', 'finished_at', 'summary'])
        SyncEventLog.objects.create(
            connection=connection,
            job=job,
            direction=SyncJob.DIRECTION_INBOUND,
            entity_type='connection_test',
            status=SyncEventLog.STATUS_PROCESSED,
            payload_excerpt=result,
        )
        record_audit_event(
            event_type='integrations.erpnext_tested',
            request=request,
            actor=request.user,
            target=connection,
            message='ERPNext connection tested successfully.',
            metadata=result,
        )
        return Response({'result': result})


class ERPNextPreviewAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
        serializer = IntegrationPreviewQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        resource = serializer.validated_data['resource']
        limit = serializer.validated_data['limit']
        client = build_erpnext_client(connection)

        try:
            if resource == 'items':
                preview = client.preview_items(limit=limit)
            elif resource == 'stock':
                preview = client.preview_stock(limit=limit)
            else:
                preview = client.preview_prices(limit=limit)
        except ERPNextIntegrationError as exc:
            raise serializers.ValidationError({'connection': str(exc)}) from exc

        return Response(
            {
                'resource': preview.resource,
                'count': preview.count,
                'records': preview.records,
            }
        )


class ERPNextCatalogImportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
        serializer = ERPNextImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            summary = ERPNextSyncService(connection).import_catalog(
                actor=request.user,
                include_stock=serializer.validated_data['include_stock'],
            )
        except ERPNextIntegrationError as exc:
            raise serializers.ValidationError({'connection': str(exc)}) from exc

        record_audit_event(
            event_type='integrations.erpnext_catalog_imported',
            request=request,
            actor=request.user,
            target=connection,
            message='ERPNext catalog import completed.',
            metadata=summary,
        )
        return Response({'summary': summary}, status=status.HTTP_201_CREATED)


class ERPNextStockSyncAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(IntegrationConnection, id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
        try:
            summary = ERPNextSyncService(connection).sync_stock(actor=request.user)
        except ERPNextIntegrationError as exc:
            raise serializers.ValidationError({'connection': str(exc)}) from exc

        record_audit_event(
            event_type='integrations.erpnext_stock_synced',
            request=request,
            actor=request.user,
            target=connection,
            message='ERPNext stock sync completed.',
            metadata=summary,
        )
        return Response({'summary': summary})
