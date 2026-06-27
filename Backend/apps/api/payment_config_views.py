from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q, Sum
from urllib.parse import urlsplit, urlunsplit
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.common.async_utils import dispatch_background_task
from apps.integrations.tasks import export_refund_credit_note_to_erpnext
from apps.notifications.secret_store import seal_secret
from apps.payments.config import (
    get_payment_setting,
    has_payment_secret,
    provider_is_configured,
    provider_is_enabled,
    provider_missing_requirements,
)
from apps.payments.models import PaymentEvent, PaymentProviderConfiguration, PaymentSession
from apps.payments.pesapal import PesapalConfigurationError, PesapalGatewayError, request_refund as request_pesapal_refund
from apps.payments.services import log_payment_event, payment_reconciliation


class MpesaConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    base_url = serializers.URLField(required=False, allow_blank=True)
    consumer_key = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    consumer_secret = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    shortcode = serializers.CharField(required=False, allow_blank=True, max_length=40)
    passkey = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    transaction_type = serializers.CharField(required=False, allow_blank=True, max_length=80)
    timeout_seconds = serializers.IntegerField(required=False, min_value=1, max_value=120)

    def validate_base_url(self, value):
        value = (value or '').strip()
        if not value:
            return value
        parsed = urlsplit(value)
        return urlunsplit((parsed.scheme, parsed.netloc, '', '', '')).rstrip('/')


class PesapalConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    base_url = serializers.URLField(required=False, allow_blank=True)
    consumer_key = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    consumer_secret = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    cancellation_url = serializers.URLField(required=False, allow_blank=True)
    ipn_url = serializers.URLField(required=False, allow_blank=True)
    ipn_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    notification_type = serializers.ChoiceField(required=False, choices=['GET', 'POST'])
    branch = serializers.CharField(required=False, allow_blank=True, max_length=120)
    redirect_mode = serializers.CharField(required=False, allow_blank=True, max_length=40)
    timeout_seconds = serializers.IntegerField(required=False, min_value=1, max_value=120)


class AirtelMoneyConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    provider_name = serializers.CharField(required=False, allow_blank=True, max_length=80)


class CardConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    provider_name = serializers.CharField(required=False, allow_blank=True, max_length=80)


class PaymentRefundRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
    refund_reference = serializers.CharField(required=False, allow_blank=True, max_length=80)
    submit_gateway_refund = serializers.BooleanField(required=False, default=True)

    def validate_refund_reference(self, value):
        return (value or '').strip()

    def validate_reason(self, value):
        return (value or '').strip()


def _serialize_provider(provider: str) -> dict:
    if provider == 'mpesa':
        is_enabled = provider_is_enabled('mpesa', default=True)
        is_configured = provider_is_configured('mpesa')
        return {
            'is_enabled': is_enabled,
            'is_configured': is_configured,
            'checkout_visible': bool(is_enabled and is_configured),
            'missing_requirements': provider_missing_requirements('mpesa'),
            'base_url': get_payment_setting('mpesa', 'base_url', settings.MPESA_BASE_URL),
            'has_consumer_key': has_payment_secret('mpesa', 'consumer_key'),
            'has_consumer_secret': has_payment_secret('mpesa', 'consumer_secret'),
            'shortcode': get_payment_setting('mpesa', 'shortcode', settings.MPESA_SHORTCODE),
            'has_passkey': has_payment_secret('mpesa', 'passkey'),
            'callback_url': get_payment_setting('mpesa', 'callback_url', settings.MPESA_CALLBACK_URL),
            'transaction_type': get_payment_setting('mpesa', 'transaction_type', settings.MPESA_TRANSACTION_TYPE),
            'timeout_seconds': int(get_payment_setting('mpesa', 'timeout_seconds', settings.MPESA_TIMEOUT_SECONDS)),
        }
    if provider == 'pesapal':
        is_enabled = provider_is_enabled('pesapal', default=True)
        is_configured = provider_is_configured('pesapal')
        return {
            'is_enabled': is_enabled,
            'is_configured': is_configured,
            'checkout_visible': bool(is_enabled and is_configured),
            'missing_requirements': provider_missing_requirements('pesapal'),
            'base_url': get_payment_setting('pesapal', 'base_url', settings.PESAPAL_BASE_URL),
            'has_consumer_key': has_payment_secret('pesapal', 'consumer_key'),
            'has_consumer_secret': has_payment_secret('pesapal', 'consumer_secret'),
            'callback_url': get_payment_setting('pesapal', 'callback_url', settings.PESAPAL_CALLBACK_URL),
            'cancellation_url': get_payment_setting('pesapal', 'cancellation_url', settings.PESAPAL_CANCELLATION_URL),
            'ipn_url': get_payment_setting('pesapal', 'ipn_url', settings.PESAPAL_IPN_URL),
            'ipn_id': get_payment_setting('pesapal', 'ipn_id', settings.PESAPAL_IPN_ID),
            'notification_type': get_payment_setting('pesapal', 'notification_type', settings.PESAPAL_IPN_NOTIFICATION_TYPE),
            'branch': get_payment_setting('pesapal', 'branch', settings.PESAPAL_BRANCH),
            'redirect_mode': get_payment_setting('pesapal', 'redirect_mode', settings.PESAPAL_REDIRECT_MODE),
            'timeout_seconds': int(get_payment_setting('pesapal', 'timeout_seconds', settings.PESAPAL_TIMEOUT_SECONDS)),
        }
    if provider == 'airtel_money':
        is_enabled = provider_is_enabled('airtel_money', default=True)
        is_configured = provider_is_configured('airtel_money')
        return {
            'is_enabled': is_enabled,
            'is_configured': is_configured,
            'checkout_visible': bool(is_enabled and is_configured),
            'missing_requirements': provider_missing_requirements('airtel_money'),
            'provider_name': get_payment_setting('airtel_money', 'provider_name', settings.AIRTEL_MONEY_PROVIDER_NAME),
            'sandbox_enabled': bool(settings.AIRTEL_MONEY_SANDBOX_ENABLED),
        }
    is_enabled = provider_is_enabled('card', default=True)
    is_configured = provider_is_configured('card')
    return {
        'is_enabled': is_enabled,
        'is_configured': is_configured,
        'checkout_visible': bool(is_enabled and is_configured),
        'missing_requirements': provider_missing_requirements('card'),
        'provider_name': get_payment_setting('card', 'provider_name', settings.CARD_PROVIDER_NAME),
        'sandbox_enabled': bool(settings.CARD_SANDBOX_ENABLED),
    }


def _upsert_provider(provider: str, *, is_enabled: bool | None, public_config: dict, secret_config: dict, user):
    config, _ = PaymentProviderConfiguration.objects.get_or_create(provider=provider)
    if is_enabled is not None:
        config.is_enabled = is_enabled

    next_public = config.public_config.copy()
    for key, value in public_config.items():
        next_public[key] = value
    config.public_config = next_public

    next_secret = config.secret_config.copy()
    for key, value in secret_config.items():
        if value:
            next_secret[key] = seal_secret(value)
    config.secret_config = next_secret
    config.updated_by = user
    config.save()
    return config


def _update_payment_configuration(request) -> Response:
    changed = []

    if 'mpesa' in request.data:
        serializer = MpesaConfigSerializer(data=request.data.get('mpesa') or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _upsert_provider(
            'mpesa',
            is_enabled=data.get('is_enabled'),
            public_config={
                key: data[key]
                for key in ['base_url', 'shortcode', 'callback_url', 'transaction_type', 'timeout_seconds']
                if key in data
            },
            secret_config={
                key: data[key]
                for key in ['consumer_key', 'consumer_secret', 'passkey']
                if key in data
            },
            user=request.user,
        )
        changed.append('mpesa')

    if 'pesapal' in request.data:
        serializer = PesapalConfigSerializer(data=request.data.get('pesapal') or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _upsert_provider(
            'pesapal',
            is_enabled=data.get('is_enabled'),
            public_config={
                key: data[key]
                for key in [
                    'base_url',
                    'callback_url',
                    'cancellation_url',
                    'ipn_url',
                    'ipn_id',
                    'notification_type',
                    'branch',
                    'redirect_mode',
                    'timeout_seconds',
                ]
                if key in data
            },
            secret_config={
                key: data[key]
                for key in ['consumer_key', 'consumer_secret']
                if key in data
            },
            user=request.user,
        )
        changed.append('pesapal')

    if 'airtel_money' in request.data:
        serializer = AirtelMoneyConfigSerializer(data=request.data.get('airtel_money') or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _upsert_provider(
            'airtel_money',
            is_enabled=data.get('is_enabled'),
            public_config={key: data[key] for key in ['provider_name'] if key in data},
            secret_config={},
            user=request.user,
        )
        changed.append('airtel_money')

    if 'card' in request.data:
        serializer = CardConfigSerializer(data=request.data.get('card') or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _upsert_provider(
            'card',
            is_enabled=data.get('is_enabled'),
            public_config={key: data[key] for key in ['provider_name'] if key in data},
            secret_config={},
            user=request.user,
        )
        changed.append('card')

    if changed:
        record_audit_event(
            event_type='payments.configuration_updated',
            request=request,
            actor=request.user,
            target=request.user,
            message='Payment provider configuration updated.',
            metadata={'providers': changed},
        )

    return Response(
        {
            'mpesa': _serialize_provider('mpesa'),
            'pesapal': _serialize_provider('pesapal'),
            'airtel_money': _serialize_provider('airtel_money'),
            'card': _serialize_provider('card'),
        }
    )


class AdminPaymentConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(
            {
                'mpesa': _serialize_provider('mpesa'),
                'pesapal': _serialize_provider('pesapal'),
                'airtel_money': _serialize_provider('airtel_money'),
                'card': _serialize_provider('card'),
            }
        )

    def patch(self, request):
        return _update_payment_configuration(request)


def _payment_session_payload(payment: PaymentSession) -> dict:
    reconciliation = payment_reconciliation(payment)
    return {
        'id': payment.id,
        'reference': payment.reference,
        'method': payment.method,
        'provider': payment.provider,
        'status': payment.status,
        'amount': float(payment.amount),
        'currency': payment.currency,
        'payer_email': payment.payer_email,
        'payer_phone': payment.payer_phone,
        'external_reference': payment.external_reference,
        'order_number': payment.order.number if payment.order_id else '',
        'metadata': payment.metadata or {},
        'provider_payload': _safe_provider_payload(payment.provider_payload or {}),
        'reconciliation': reconciliation,
        'events': [_payment_event_payload(event) for event in list(getattr(payment, 'prefetched_events', []))[:8]],
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
        'paid_at': payment.paid_at,
    }


def _payment_event_payload(event: PaymentEvent) -> dict:
    return {
        'id': event.id,
        'kind': event.kind,
        'status_before': event.status_before,
        'status_after': event.status_after,
        'external_reference': event.external_reference,
        'message': event.message,
        'payload': _safe_provider_payload(event.payload or {}),
        'created_at': event.created_at,
    }


def _safe_provider_payload(payload: dict) -> dict:
    hidden_keys = {'consumer_key', 'consumer_secret', 'passkey', 'token', 'access_token', 'password', 'secret'}
    safe = {}
    for key, value in payload.items():
        normalized = str(key).lower()
        if any(secret_key in normalized for secret_key in hidden_keys):
            safe[key] = '***'
        elif key == 'pesapal_response' and isinstance(value, dict):
            safe[key] = _safe_provider_payload(value)
        elif key == 'last_status' and isinstance(value, dict):
            safe[key] = _safe_provider_payload(value)
        else:
            safe[key] = value
    return safe


def _matches_reconciliation_filter(payment: PaymentSession, reconciliation_filter: str) -> bool:
    if not reconciliation_filter:
        return True
    reconciliation = payment_reconciliation(payment)
    if reconciliation_filter == 'needs_attention':
        return bool(reconciliation.get('needs_attention'))
    return reconciliation.get('status') == reconciliation_filter


def _reconciliation_summary(queryset) -> dict:
    counts = {}
    needs_attention = 0
    for payment in queryset.select_related('order'):
        reconciliation = payment_reconciliation(payment)
        key = reconciliation['status']
        counts[key] = counts.get(key, 0) + 1
        if reconciliation.get('needs_attention'):
            needs_attention += 1
    return {'counts': counts, 'needs_attention': needs_attention}


class AdminPaymentSessionLogCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = (
            PaymentSession.objects.select_related('user', 'order')
            .prefetch_related(
                Prefetch(
                    'events',
                    queryset=PaymentEvent.objects.order_by('-created_at', '-id'),
                    to_attr='prefetched_events',
                )
            )
            .order_by('-created_at')
        )

        search = (request.query_params.get('q') or '').strip()
        method = (request.query_params.get('method') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        provider = (request.query_params.get('provider') or '').strip()
        reconciliation_filter = (request.query_params.get('reconciliation') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search)
                | Q(external_reference__icontains=search)
                | Q(payer_email__icontains=search)
                | Q(payer_phone__icontains=search)
                | Q(order__number__icontains=search)
            )
        if method:
            queryset = queryset.filter(method=method)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if provider:
            queryset = queryset.filter(provider=provider)
        if reconciliation_filter:
            queryset = [
                payment
                for payment in queryset
                if _matches_reconciliation_filter(payment, reconciliation_filter)
            ]

        page = max(1, int(request.query_params.get('page') or 1))
        page_size = min(100, max(1, int(request.query_params.get('page_size') or 50)))
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        base_queryset = PaymentSession.objects.all()
        summary = {
            'total': base_queryset.count(),
            'by_status': list(base_queryset.values('status').annotate(count=Count('id')).order_by('status')),
            'by_method': list(base_queryset.values('method').annotate(count=Count('id')).order_by('method')),
            'paid_total': float(base_queryset.filter(status=PaymentSession.STATUS_PAID).aggregate(total=Sum('amount'))['total'] or 0),
            'authorized_total': float(base_queryset.filter(status=PaymentSession.STATUS_AUTHORIZED).aggregate(total=Sum('amount'))['total'] or 0),
            'reconciliation': _reconciliation_summary(base_queryset),
        }

        return Response(
            {
                'results': [_payment_session_payload(payment) for payment in page_obj.object_list],
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'num_pages': paginator.num_pages,
                    'count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'summary': summary,
            }
        )


class AdminPaymentRefundAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, reference: str):
        payment = get_payment_or_404(reference)
        serializer = PaymentRefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if payment.status not in {PaymentSession.STATUS_PAID, PaymentSession.STATUS_AUTHORIZED}:
            return Response({'detail': 'Only paid or authorized payments can be sent for refund accounting.'}, status=status.HTTP_400_BAD_REQUEST)
        if not payment.order_id:
            return Response({'detail': 'This payment is not linked to an order.'}, status=status.HTTP_400_BAD_REQUEST)

        refund_amount = serializer.validated_data.get('amount') or payment.amount
        reason = serializer.validated_data.get('reason') or 'Refund requested by staff.'
        refund_reference = serializer.validated_data.get('refund_reference') or f'REFUND-{payment.reference}'
        submit_gateway_refund = serializer.validated_data.get('submit_gateway_refund', True)
        metadata = payment.metadata or {}
        refund_requests = metadata.get('refund_requests') or []
        if any(item.get('refund_reference') == refund_reference for item in refund_requests):
            return Response({'detail': 'Refund request already recorded.', 'refund_reference': refund_reference}, status=status.HTTP_200_OK)

        gateway_response = None
        if submit_gateway_refund and payment.method == PaymentSession.METHOD_PESAPAL:
            try:
                gateway_response = request_pesapal_refund(
                    payment,
                    amount=refund_amount,
                    username=request.user.get_full_name() or request.user.email or request.user.username,
                    remarks=reason,
                )
            except (PesapalConfigurationError, PesapalGatewayError) as exc:
                log_payment_event(
                    payment,
                    kind='gateway_error',
                    status_before=payment.status,
                    status_after=payment.status,
                    external_reference=payment.external_reference,
                    message=str(exc),
                    payload={'phase': 'pesapal_refund_request', 'refund_reference': refund_reference},
                )
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            log_payment_event(
                payment,
                kind='provider_submitted',
                status_before=payment.status,
                status_after=payment.status,
                external_reference=payment.external_reference,
                message='Pesapal refund request submitted.',
                payload={'phase': 'pesapal_refund_request', 'refund_reference': refund_reference, 'pesapal_response': gateway_response},
            )

        refund_requests.append(
            {
                'refund_reference': refund_reference,
                'amount': str(refund_amount),
                'reason': reason,
                'requested_by': request.user.id,
                'gateway': payment.method if submit_gateway_refund else 'manual',
                'gateway_response': gateway_response or {},
            }
        )
        payment.metadata = {**metadata, 'refund_requests': refund_requests}
        payment.save(update_fields=['metadata', 'updated_at'])

        dispatch_background_task(
            export_refund_credit_note_to_erpnext,
            run_kwargs={
                'payment_reference': payment.reference,
                'refund_amount': str(refund_amount),
                'reason': reason,
                'refund_reference': refund_reference,
            },
            async_kwargs={
                'payment_reference': payment.reference,
                'refund_amount': str(refund_amount),
                'reason': reason,
                'refund_reference': refund_reference,
            },
        )
        record_audit_event(
            event_type='payments.refund_requested',
            request=request,
            actor=request.user,
            target=payment,
            message='Staff requested refund accounting export.',
            metadata={'payment_reference': payment.reference, 'refund_reference': refund_reference, 'amount': str(refund_amount)},
        )
        return Response({'detail': 'Refund accounting export queued.', 'refund_reference': refund_reference}, status=status.HTTP_202_ACCEPTED)


def get_payment_or_404(reference: str):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(PaymentSession.objects.select_related('order'), reference=reference)
