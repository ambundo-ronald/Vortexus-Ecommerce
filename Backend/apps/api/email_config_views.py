from django.apps import apps
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.notifications.config import (
    build_email_connection,
    configured_from_email,
    configured_reply_to_email,
    email_configured_for_delivery,
    get_email_configuration,
)
from apps.notifications.models import EmailConfiguration, EmailNotification, EmailSuppression
from apps.notifications.services import retry_email_notification
from apps.notifications.templates import ensure_custom_communication_templates


class AdminEmailConfigurationSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    host = serializers.CharField(required=False, allow_blank=True, max_length=255)
    port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    username = serializers.CharField(required=False, allow_blank=True, max_length=255)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    use_tls = serializers.BooleanField(required=False)
    use_ssl = serializers.BooleanField(required=False)
    timeout_seconds = serializers.IntegerField(required=False, min_value=1, max_value=120)
    from_email = serializers.EmailField(required=False, allow_blank=True)
    reply_to_email = serializers.EmailField(required=False, allow_blank=True)
    sales_recipients = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        use_tls = attrs.get('use_tls')
        use_ssl = attrs.get('use_ssl')
        instance = get_email_configuration()
        effective_tls = use_tls if use_tls is not None else bool(getattr(instance, 'use_tls', True))
        effective_ssl = use_ssl if use_ssl is not None else bool(getattr(instance, 'use_ssl', False))
        if effective_tls and effective_ssl:
            raise serializers.ValidationError({'use_ssl': 'Choose either TLS or SSL, not both.'})
        return attrs


class TestEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField(required=False, allow_blank=True)


class AdminEmailSuppressionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reason = serializers.ChoiceField(choices=[choice[0] for choice in EmailSuppression.REASON_CHOICES], required=False)
    source = serializers.CharField(required=False, allow_blank=True, max_length=64)
    note = serializers.CharField(required=False, allow_blank=True)


class AdminEmailTemplateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=False, max_length=128)
    category = serializers.CharField(required=False, allow_blank=True, max_length=64)
    email_subject_template = serializers.CharField(required=False, allow_blank=True)
    email_body_template = serializers.CharField(required=False, allow_blank=True)
    email_body_html_template = serializers.CharField(required=False, allow_blank=True)


def _serialize_email_config(config=None) -> dict:
    config = config or get_email_configuration()
    if not config:
        return {
            'is_enabled': False,
            'is_configured': False,
            'host': '',
            'port': 587,
            'username': '',
            'has_password': False,
            'password_protected': False,
            'use_tls': True,
            'use_ssl': False,
            'timeout_seconds': 30,
            'from_email': '',
            'reply_to_email': '',
            'sales_recipients': '',
        }

    return {
        'is_enabled': config.is_enabled,
        'is_configured': email_configured_for_delivery(),
        'host': config.host,
        'port': config.port,
        'username': config.username,
        'has_password': bool(config.password),
        'password_protected': bool(config.password and config.password_is_protected),
        'use_tls': config.use_tls,
        'use_ssl': config.use_ssl,
        'timeout_seconds': config.timeout_seconds,
        'from_email': config.from_email,
        'reply_to_email': config.reply_to_email,
        'sales_recipients': config.sales_recipients,
        'updated_at': config.updated_at,
    }


def _get_or_create_config():
    config, _ = EmailConfiguration.objects.get_or_create(provider='smtp')
    return config


class AdminEmailConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response({'email': _serialize_email_config()})

    def patch(self, request):
        serializer = AdminEmailConfigurationSerializer(data=request.data.get('email') or request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        config = _get_or_create_config()
        data = serializer.validated_data
        for field in [
            'is_enabled',
            'host',
            'port',
            'username',
            'use_tls',
            'use_ssl',
            'timeout_seconds',
            'from_email',
            'reply_to_email',
            'sales_recipients',
        ]:
            if field in data:
                setattr(config, field, data[field])
        if data.get('password'):
            config.set_password_secret(data['password'])
        config.updated_by = request.user
        config.save()

        record_audit_event(
            event_type='email.configuration_updated',
            request=request,
            actor=request.user,
            target=request.user,
            message='Email deliverability configuration updated.',
            metadata={'enabled': config.is_enabled, 'host': config.host, 'from_email': config.from_email},
        )

        return Response({'email': _serialize_email_config(config)})


class AdminEmailTestAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = TestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient = serializer.validated_data.get('recipient') or request.user.email
        if not recipient:
            raise serializers.ValidationError({'recipient': 'Recipient email is required.'})

        try:
            message = EmailMultiAlternatives(
                subject='Reesolmart email test',
                body='This is a test email from the Reesolmart admin dashboard.',
                from_email=configured_from_email(),
                to=[recipient],
                reply_to=[configured_reply_to_email()] if configured_reply_to_email() else None,
                connection=build_email_connection(),
            )
            sent = message.send()
        except Exception as exc:
            record_audit_event(
                event_type='email.test_failed',
                request=request,
                actor=request.user,
                target=request.user,
                message='Email test failed.',
                metadata={'recipient': recipient, 'error': str(exc)},
                status='failure',
            )
            return Response(
                {'error': {'code': 'email_test_failed', 'detail': str(exc), 'status': 502}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        record_audit_event(
            event_type='email.test_sent',
            request=request,
            actor=request.user,
            target=request.user,
            message='Email test sent.',
            metadata={'recipient': recipient, 'sent': sent},
        )
        return Response({'detail': f'Test email sent to {recipient}.', 'sent': sent})


def _email_notification_payload(notification: EmailNotification) -> dict:
    return {
        'id': notification.id,
        'event_type': notification.event_type,
        'status': notification.status,
        'recipient': notification.recipient,
        'subject': notification.subject,
        'related_object_type': notification.related_object_type,
        'related_object_id': notification.related_object_id,
        'error_message': notification.error_message,
        'metadata': notification.metadata or {},
        'sent_at': notification.sent_at,
        'created_at': notification.created_at,
        'updated_at': notification.updated_at,
    }


def _email_suppression_payload(suppression: EmailSuppression) -> dict:
    return {
        'id': suppression.id,
        'email': suppression.email,
        'reason': suppression.reason,
        'source': suppression.source,
        'note': suppression.note,
        'metadata': suppression.metadata or {},
        'created_by': suppression.created_by.email if suppression.created_by_id and suppression.created_by else '',
        'created_at': suppression.created_at,
        'updated_at': suppression.updated_at,
    }


def _communication_model():
    ensure_custom_communication_templates()
    return apps.get_model('communication', 'CommunicationEventType')


def _email_template_payload(template) -> dict:
    return {
        'id': template.id,
        'code': template.code,
        'name': template.name,
        'category': template.category,
        'email_subject_template': template.email_subject_template,
        'email_body_template': template.email_body_template,
        'email_body_html_template': template.email_body_html_template,
        'sms_template': template.sms_template,
    }


class AdminEmailLogCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = EmailNotification.objects.all()

        query = (request.query_params.get('q') or '').strip()
        event_type = (request.query_params.get('event_type') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        recipient = (request.query_params.get('recipient') or '').strip()
        related_object_type = (request.query_params.get('related_object_type') or '').strip()
        related_object_id = (request.query_params.get('related_object_id') or '').strip()
        date_from = (request.query_params.get('date_from') or '').strip()
        date_to = (request.query_params.get('date_to') or '').strip()

        if query:
            queryset = queryset.filter(
                Q(event_type__icontains=query)
                | Q(status__icontains=query)
                | Q(recipient__icontains=query)
                | Q(subject__icontains=query)
                | Q(related_object_type__icontains=query)
                | Q(related_object_id__icontains=query)
                | Q(error_message__icontains=query)
            )
        if event_type:
            queryset = queryset.filter(event_type__icontains=event_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if recipient:
            queryset = queryset.filter(recipient__icontains=recipient)
        if related_object_type:
            queryset = queryset.filter(related_object_type__icontains=related_object_type)
        if related_object_id:
            queryset = queryset.filter(related_object_id__icontains=related_object_id)
        if date_from:
            parsed_from = parse_datetime(date_from) or parse_date(date_from)
            if parsed_from:
                queryset = queryset.filter(created_at__gte=parsed_from)
        if date_to:
            parsed_to = parse_datetime(date_to) or parse_date(date_to)
            if parsed_to:
                queryset = queryset.filter(created_at__lte=parsed_to)

        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 50) or 50), 1), 200)
        except (TypeError, ValueError):
            return Response(
                {'error': {'code': 'invalid_pagination', 'detail': 'Page and page_size must be integers.', 'status': 400}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        base_queryset = EmailNotification.objects.all()
        status_counts = {row['status']: row['count'] for row in base_queryset.values('status').annotate(count=Count('id'))}
        event_counts = {
            row['event_type']: row['count']
            for row in base_queryset.values('event_type').annotate(count=Count('id')).order_by('event_type')
        }

        return Response(
            {
                'results': [_email_notification_payload(notification) for notification in page_obj.object_list],
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': base_queryset.count(),
                    'sent': status_counts.get('sent', 0),
                    'failed': status_counts.get('failed', 0),
                    'skipped': status_counts.get('skipped', 0),
                    'pending': status_counts.get('pending', 0),
                    'events': event_counts,
                },
            }
        )


class AdminEmailLogDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, notification_id: int):
        notification = get_object_or_404(EmailNotification, id=notification_id)
        return Response({'email_log': _email_notification_payload(notification)})


class AdminEmailLogRetryAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, notification_id: int):
        notification = get_object_or_404(EmailNotification, id=notification_id)
        try:
            sent = retry_email_notification(notification, raise_on_failure=True)
        except ValueError as exc:
            record_audit_event(
                event_type='email.retry_rejected',
                request=request,
                actor=request.user,
                target=notification,
                message='Email retry was rejected.',
                metadata={'email_log_id': notification.id, 'event_type': notification.event_type, 'error': str(exc)},
                status='failure',
            )
            return Response(
                {'error': {'code': 'email_retry_rejected', 'detail': str(exc), 'status': 400}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            record_audit_event(
                event_type='email.retry_failed',
                request=request,
                actor=request.user,
                target=notification,
                message='Email retry failed.',
                metadata={'email_log_id': notification.id, 'event_type': notification.event_type, 'error': str(exc)},
                status='failure',
            )
            return Response(
                {'error': {'code': 'email_retry_failed', 'detail': str(exc), 'status': 502}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        record_audit_event(
            event_type='email.retry_sent',
            request=request,
            actor=request.user,
            target=notification,
            message='Email retry sent.',
            metadata={'email_log_id': notification.id, 'event_type': notification.event_type, 'sent': sent},
        )
        return Response({'detail': 'Email retry sent.', 'sent': sent})


class AdminEmailSuppressionCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = EmailSuppression.objects.all()
        query = (request.query_params.get('q') or '').strip()
        reason = (request.query_params.get('reason') or '').strip()
        if query:
            queryset = queryset.filter(Q(email__icontains=query) | Q(note__icontains=query) | Q(source__icontains=query))
        if reason:
            queryset = queryset.filter(reason=reason)

        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 50) or 50), 1), 200)
        except (TypeError, ValueError):
            return Response(
                {'error': {'code': 'invalid_pagination', 'detail': 'Page and page_size must be integers.', 'status': 400}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        reason_counts = {row['reason']: row['count'] for row in EmailSuppression.objects.values('reason').annotate(count=Count('id'))}
        return Response(
            {
                'results': [_email_suppression_payload(item) for item in page_obj.object_list],
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': EmailSuppression.objects.count(),
                    'bounce': reason_counts.get('bounce', 0),
                    'complaint': reason_counts.get('complaint', 0),
                    'manual': reason_counts.get('manual', 0),
                    'unsubscribe': reason_counts.get('unsubscribe', 0),
                },
            }
        )

    def post(self, request):
        serializer = AdminEmailSuppressionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        suppression, created = EmailSuppression.objects.update_or_create(
            email=data['email'].strip().lower(),
            defaults={
                'reason': data.get('reason') or 'manual',
                'source': data.get('source', 'admin'),
                'note': data.get('note', ''),
                'created_by': request.user,
            },
        )
        record_audit_event(
            event_type='email.suppression_created' if created else 'email.suppression_updated',
            request=request,
            actor=request.user,
            target=suppression,
            message='Email suppression list updated.',
            metadata={'email': suppression.email, 'reason': suppression.reason, 'source': suppression.source},
        )
        return Response({'suppression': _email_suppression_payload(suppression)}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AdminEmailSuppressionDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, suppression_id: int):
        suppression = get_object_or_404(EmailSuppression, id=suppression_id)
        payload = _email_suppression_payload(suppression)
        suppression.delete()
        record_audit_event(
            event_type='email.suppression_deleted',
            request=request,
            actor=request.user,
            target=request.user,
            message='Email suppression was removed.',
            metadata={'email': payload['email'], 'reason': payload['reason']},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminEmailTemplateCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        CommunicationEventType = _communication_model()
        query = (request.query_params.get('q') or '').strip()
        queryset = CommunicationEventType.objects.exclude(email_subject_template='', email_body_template='')
        if query:
            queryset = queryset.filter(Q(code__icontains=query) | Q(name__icontains=query) | Q(category__icontains=query))
        queryset = queryset.order_by('category', 'name', 'code')
        return Response({'results': [_email_template_payload(template) for template in queryset]})


class AdminEmailTemplateDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, code: str):
        CommunicationEventType = _communication_model()
        template = get_object_or_404(CommunicationEventType, code=code)
        return Response({'template': _email_template_payload(template)})

    def patch(self, request, code: str):
        serializer = AdminEmailTemplateSerializer(data=request.data.get('template') or request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        CommunicationEventType = _communication_model()
        template = get_object_or_404(CommunicationEventType, code=code)
        for field, value in serializer.validated_data.items():
            setattr(template, field, value)
        template.save()
        record_audit_event(
            event_type='email.template_updated',
            request=request,
            actor=request.user,
            target=request.user,
            message='Email template updated.',
            metadata={'code': template.code, 'name': template.name},
        )
        return Response({'template': _email_template_payload(template)})
