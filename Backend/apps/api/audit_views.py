from django.apps import apps
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit_serializers import AuditLogSerializer


class AuditLogCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        AuditLog = apps.get_model('auditlog', 'AuditLog')
        queryset = AuditLog.objects.select_related('actor').all()

        event_type = (request.query_params.get('event_type') or '').strip()
        actor_email = (request.query_params.get('actor_email') or '').strip()
        target_type = (request.query_params.get('target_type') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if actor_email:
            queryset = queryset.filter(actor_email__icontains=actor_email)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 50) or 50), 1), 200)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': {
                        'code': 'invalid_pagination',
                        'detail': 'Page and page_size must be integers.',
                        'status': 400,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = AuditLogSerializer(page_obj.object_list, many=True)
        return Response(
            {
                'results': serializer.data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class AuditLogDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, audit_log_id: int):
        AuditLog = apps.get_model('auditlog', 'AuditLog')
        audit_log = get_object_or_404(AuditLog.objects.select_related('actor'), id=audit_log_id)
        return Response({'audit_log': AuditLogSerializer(audit_log).data})
