import csv
from decimal import Decimal
from io import StringIO
from django.apps import apps
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Count, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from urllib.parse import urlsplit, urlunsplit
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.common.async_utils import dispatch_background_task
from apps.integrations.tasks import export_refund_credit_note_to_erpnext, export_supplier_payout_batch_to_erpnext
from apps.marketplace.payables import (
    approve_supplier_payout_batch,
    cancel_supplier_payout_batch,
    create_supplier_debit_adjustments_for_refund,
    create_supplier_payout_batch,
    mark_supplier_payout_batch_paid,
    submit_supplier_payout_batch,
)
from apps.notifications.secret_store import seal_secret
from apps.payments.config import (
    get_payment_setting,
    has_payment_secret,
    provider_is_configured,
    provider_is_enabled,
    provider_missing_requirements,
)
from apps.payments.models import PaymentEvent, PaymentProviderConfiguration, PaymentReconciliation, PaymentRefundLedger, PaymentReturnCase, PaymentSession
from apps.payments.mpesa import MpesaConfigurationError, MpesaGatewayError, initiate_stk_push, mpesa_is_configured
from apps.payments.pesapal import (
    PesapalConfigurationError,
    PesapalGatewayError,
    register_ipn_url,
    request_refund as request_pesapal_refund,
)
from apps.payments.services import (
    create_payment_return_case,
    initialize_payment_session,
    log_payment_event,
    payment_reconciliation,
    record_payment_refund_ledger,
    update_payment_return_case,
    serialize_payment_session,
)

from .account_manager_scope import can_access_all_admin_data, can_access_finance_data, scope_orders_queryset, scope_payment_sessions_queryset


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


class CashOnDeliveryConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    requires_customer_approval = serializers.BooleanField(required=False)
    prompt_before_dispatch = serializers.BooleanField(required=False)


class PaymentRefundRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
    refund_reference = serializers.CharField(required=False, allow_blank=True, max_length=80)
    submit_gateway_refund = serializers.BooleanField(required=False, default=True)

    def validate_refund_reference(self, value):
        return (value or '').strip()

    def validate_reason(self, value):
        return (value or '').strip()


class SupplierPayoutBatchCreateSerializer(serializers.Serializer):
    payable_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    payout_method = serializers.CharField(required=False, allow_blank=True, max_length=64)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class SupplierPayoutBatchStatusSerializer(serializers.Serializer):
    payout_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)
    evidence_url = serializers.URLField(required=False, allow_blank=True)
    evidence_file = serializers.FileField(required=False, allow_empty_file=False)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class FinanceReconciliationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[choice[0] for choice in PaymentReconciliation.STATUS_CHOICES])
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class FinanceReturnCreateSerializer(serializers.Serializer):
    payment_reference = serializers.CharField(max_length=128)
    line_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    refund_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
    restock_decision = serializers.ChoiceField(required=False, choices=[choice[0] for choice in PaymentReturnCase.RESTOCK_CHOICES])
    condition_note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class FinanceReturnStatusSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'receive', 'accept', 'reject', 'refund', 'cancel'])
    accepted_quantity = serializers.IntegerField(required=False, min_value=1)
    restock_decision = serializers.ChoiceField(required=False, choices=[choice[0] for choice in PaymentReturnCase.RESTOCK_CHOICES])
    condition_note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AdminCodMpesaPromptSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=40)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=0)


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
    if provider == 'cash_on_delivery':
        is_enabled = provider_is_enabled('cash_on_delivery', default=False)
        requires_customer_approval = bool(get_payment_setting('cash_on_delivery', 'requires_customer_approval', True))
        prompt_before_dispatch = bool(get_payment_setting('cash_on_delivery', 'prompt_before_dispatch', True))
        return {
            'is_enabled': is_enabled,
            'is_configured': True,
            'checkout_visible': bool(is_enabled),
            'missing_requirements': [],
            'requires_customer_approval': requires_customer_approval,
            'prompt_before_dispatch': prompt_before_dispatch,
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

    if 'cash_on_delivery' in request.data:
        serializer = CashOnDeliveryConfigSerializer(data=request.data.get('cash_on_delivery') or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _upsert_provider(
            'cash_on_delivery',
            is_enabled=data.get('is_enabled'),
            public_config={
                key: data[key]
                for key in ['requires_customer_approval', 'prompt_before_dispatch']
                if key in data
            },
            secret_config={},
            user=request.user,
        )
        changed.append('cash_on_delivery')

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
            'cash_on_delivery': _serialize_provider('cash_on_delivery'),
        }
    )


class AdminPaymentConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_all_admin_data(request.user):
            return Response({'detail': 'Only a platform admin can view payment configuration.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                'mpesa': _serialize_provider('mpesa'),
                'pesapal': _serialize_provider('pesapal'),
                'airtel_money': _serialize_provider('airtel_money'),
                'card': _serialize_provider('card'),
                'cash_on_delivery': _serialize_provider('cash_on_delivery'),
            }
        )

    def patch(self, request):
        if not can_access_all_admin_data(request.user):
            return Response({'detail': 'Only a platform admin can update payment configuration.'}, status=status.HTTP_403_FORBIDDEN)
        return _update_payment_configuration(request)


class AdminPesapalRegisterIPNAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        if not can_access_all_admin_data(request.user):
            return Response({'detail': 'Only a platform admin can register payment callbacks.'}, status=status.HTTP_403_FORBIDDEN)
        ipn_url = (request.data.get('ipn_url') or get_payment_setting('pesapal', 'ipn_url', settings.PESAPAL_IPN_URL) or '').strip()
        notification_type = (
            request.data.get('notification_type')
            or get_payment_setting('pesapal', 'notification_type', settings.PESAPAL_IPN_NOTIFICATION_TYPE)
            or 'POST'
        ).strip().upper()

        try:
            response_data = register_ipn_url(ipn_url=ipn_url, notification_type=notification_type)
        except (PesapalConfigurationError, PesapalGatewayError) as exc:
            return Response(
                {
                    'error': {
                        'code': 'pesapal_ipn_registration_failed',
                        'detail': str(exc),
                        'status': status.HTTP_400_BAD_REQUEST,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ipn_id = str(response_data.get('ipn_id') or response_data.get('notification_id') or '').strip()
        _upsert_provider(
            'pesapal',
            is_enabled=None,
            public_config={
                'ipn_url': ipn_url,
                'notification_type': notification_type,
                'ipn_id': ipn_id,
            },
            secret_config={},
            user=request.user,
        )
        record_audit_event(
            event_type='payments.pesapal_ipn_registered',
            request=request,
            actor=request.user,
            target=request.user,
            message='Pesapal IPN URL registered.',
            metadata={'ipn_url': ipn_url, 'notification_type': notification_type, 'ipn_id': ipn_id},
        )
        return Response({'pesapal': _serialize_provider('pesapal'), 'pesapal_response': _safe_provider_payload(response_data)})


def _payment_session_payload(payment: PaymentSession) -> dict:
    reconciliation = payment_reconciliation(payment)
    ledger = getattr(payment, 'reconciliation', None)
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
        'reconciliation_ledger': _payment_reconciliation_payload(ledger) if ledger else None,
        'events': [_payment_event_payload(event) for event in list(getattr(payment, 'prefetched_events', []))[:8]],
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
        'paid_at': payment.paid_at,
    }


def _payment_reconciliation_payload(reconciliation) -> dict:
    return {
        'id': reconciliation.id,
        'status': reconciliation.status,
        'provider_reference': reconciliation.provider_reference,
        'merchant_reference': reconciliation.merchant_reference,
        'expected_amount': float(reconciliation.expected_amount or 0),
        'paid_amount': float(reconciliation.paid_amount or 0),
        'fee_amount': float(reconciliation.fee_amount or 0),
        'settled_amount': float(reconciliation.settled_amount or 0),
        'currency': reconciliation.currency,
        'issues': reconciliation.issues or [],
        'last_checked_at': reconciliation.last_checked_at,
        'review_note': reconciliation.review_note,
        'reviewed_at': reconciliation.reviewed_at,
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


def _money_total(queryset, field: str) -> float:
    return float(queryset.aggregate(total=Sum(field)).get('total') or 0)


def _refund_request_summary(payments) -> dict:
    payment_ids = list(payments.values_list('id', flat=True))
    ledger_queryset = PaymentRefundLedger.objects.filter(payment_session_id__in=payment_ids)
    ledger_count = ledger_queryset.count()
    ledger_total = Decimal(str(ledger_queryset.aggregate(total=Sum('amount')).get('total') or '0')).quantize(Decimal('0.01'))
    payments_with_ledger = set(ledger_queryset.values_list('payment_session_id', flat=True))

    refund_count = 0
    refund_total = Decimal('0.00')
    metadata_payments = payments.exclude(id__in=payments_with_ledger).select_related(None).only('metadata', 'amount')
    for payment in metadata_payments:
        for refund in (payment.metadata or {}).get('refund_requests', []):
            refund_count += 1
            refund_total += Decimal(str(refund.get('amount') or payment.amount or 0))
    return {'count': ledger_count + refund_count, 'total': float(ledger_total + refund_total)}


def _pagination_payload(page_obj, page: int, page_size: int) -> dict:
    return {
        'page': page_obj.number,
        'page_size': page_size,
        'num_pages': page_obj.paginator.num_pages,
        'count': page_obj.paginator.count,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }


def _page_queryset(request, queryset, *, default_page_size=50, max_page_size=100):
    try:
        page = max(1, int(request.query_params.get('page') or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max_page_size, max(1, int(request.query_params.get('page_size') or default_page_size)))
    except (TypeError, ValueError):
        page_size = default_page_size
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return page_obj, page_size


def _apply_date_filters(queryset, request, field_name='created_at'):
    date_from = parse_date((request.query_params.get('date_from') or '').strip())
    date_to = parse_date((request.query_params.get('date_to') or '').strip())
    if date_from:
        queryset = queryset.filter(**{f'{field_name}__date__gte': date_from})
    if date_to:
        queryset = queryset.filter(**{f'{field_name}__date__lte': date_to})
    return queryset


def _finance_reconciliation_payload(reconciliation) -> dict:
    payment = reconciliation.payment_session
    return {
        'id': reconciliation.id,
        'status': reconciliation.status,
        'provider': reconciliation.provider,
        'method': reconciliation.method,
        'merchant_reference': reconciliation.merchant_reference,
        'provider_reference': reconciliation.provider_reference,
        'expected_amount': float(reconciliation.expected_amount or 0),
        'paid_amount': float(reconciliation.paid_amount or 0),
        'fee_amount': float(reconciliation.fee_amount or 0),
        'settled_amount': float(reconciliation.settled_amount or 0),
        'currency': reconciliation.currency,
        'issues': reconciliation.issues or [],
        'order_number': reconciliation.order.number if reconciliation.order_id else '',
        'payment_reference': payment.reference if payment else '',
        'payment_status': payment.status if payment else '',
        'payer_email': payment.payer_email if payment else '',
        'payer_phone': payment.payer_phone if payment else '',
        'last_checked_at': reconciliation.last_checked_at,
        'reviewed_at': reconciliation.reviewed_at,
        'review_note': reconciliation.review_note,
        'created_at': reconciliation.created_at,
        'updated_at': reconciliation.updated_at,
    }


def _finance_payable_payload(payable) -> dict:
    allocation = getattr(payable, 'allocation', None)
    return {
        'id': payable.id,
        'status': payable.status,
        'source_status': payable.source_status,
        'supplier_id': payable.supplier_id,
        'supplier_name': payable.supplier.company_name if payable.supplier_id else payable.partner.name,
        'account_manager_id': payable.supplier.account_manager_id if payable.supplier_id else None,
        'account_manager_email': payable.supplier.account_manager.email if payable.supplier_id and payable.supplier.account_manager_id else '',
        'partner_id': payable.partner_id,
        'partner_name': payable.partner.name,
        'order_number': payable.order.number,
        'order_status': payable.order.status,
        'line_id': payable.line_id,
        'line_status': payable.line.status if payable.line_id else '',
        'product_id': payable.product_id,
        'product_title': payable.product.title if payable.product_id else payable.line.title,
        'supplier_offer_id': payable.supplier_offer_id,
        'stockrecord_id': payable.stockrecord_id,
        'quantity': payable.quantity,
        'supplier_unit_cost': float(payable.supplier_unit_cost or 0),
        'payable_total': float(payable.payable_total or 0),
        'currency': payable.currency,
        'payout_reference': payable.payout_reference,
        'reversal_reason': payable.reversal_reason,
        'erpnext_sync_status': getattr(payable, 'erpnext_sync_status', ''),
        'erpnext_reference': getattr(payable, 'erpnext_reference', ''),
        'erpnext_sync_message': getattr(payable, 'erpnext_sync_message', ''),
        'erpnext_synced_at': getattr(payable, 'erpnext_synced_at', None),
        'customer_unit_price_incl_tax': float(getattr(allocation, 'customer_unit_price_incl_tax', 0) or 0),
        'gross_margin': float(getattr(allocation, 'gross_margin', 0) or 0),
        'created_at': payable.created_at,
        'updated_at': payable.updated_at,
    }


def _finance_payout_batch_entry_payload(entry) -> dict:
    payable = entry.payable
    return {
        'id': entry.id,
        'payable_id': entry.payable_id,
        'amount': float(entry.amount or 0),
        'currency': entry.currency,
        'order_number': payable.order.number if payable.order_id else '',
        'product_title': payable.product.title if payable.product_id else payable.line.title,
        'quantity': payable.quantity,
        'supplier_name': payable.supplier.company_name if payable.supplier_id else payable.partner.name,
        'payable_status': payable.status,
        'created_at': entry.created_at,
    }


def _finance_payout_batch_payload(batch, *, include_entries=False) -> dict:
    payload = {
        'id': batch.id,
        'batch_reference': batch.batch_reference,
        'supplier_id': batch.supplier_id,
        'supplier_name': batch.supplier.company_name if batch.supplier_id else batch.partner.name if batch.partner_id else '',
        'partner_id': batch.partner_id,
        'partner_name': batch.partner.name if batch.partner_id else '',
        'status': batch.status,
        'currency': batch.currency,
        'total_amount': float(batch.total_amount or 0),
        'entry_count': batch.entry_count,
        'payout_method': batch.payout_method,
        'payout_reference': batch.payout_reference,
        'evidence_url': batch.evidence_url,
        'evidence_file_url': batch.evidence_file.url if getattr(batch, 'evidence_file', None) else '',
        'notes': batch.notes,
        'erpnext_sync_status': getattr(batch, 'erpnext_sync_status', ''),
        'erpnext_reference': getattr(batch, 'erpnext_reference', ''),
        'erpnext_sync_message': getattr(batch, 'erpnext_sync_message', ''),
        'erpnext_synced_at': getattr(batch, 'erpnext_synced_at', None),
        'created_by_email': batch.created_by.email if batch.created_by_id else '',
        'approved_by_email': batch.approved_by.email if batch.approved_by_id else '',
        'paid_by_email': batch.paid_by.email if batch.paid_by_id else '',
        'approved_at': batch.approved_at,
        'paid_at': batch.paid_at,
        'created_at': batch.created_at,
        'updated_at': batch.updated_at,
    }
    if include_entries:
        payload['entries'] = [_finance_payout_batch_entry_payload(entry) for entry in batch.entries.all()]
    return payload


def _finance_payment_payload(payment: PaymentSession) -> dict:
    return {
        'id': payment.id,
        'reference': payment.reference,
        'method': payment.method,
        'provider': payment.provider,
        'status': payment.status,
        'amount': float(payment.amount or 0),
        'currency': payment.currency,
        'payer_email': payment.payer_email,
        'payer_phone': payment.payer_phone,
        'external_reference': payment.external_reference,
        'paid_at': payment.paid_at,
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
    }


def _finance_refund_payload(refund) -> dict:
    return {
        'id': getattr(refund, 'id', None),
        'payment_reference': refund.payment_session.reference if getattr(refund, 'payment_session_id', None) else '',
        'order_number': refund.order.number if getattr(refund, 'order_id', None) else '',
        'refund_reference': refund.refund_reference,
        'refund_type': refund.refund_type,
        'status': refund.status,
        'refund_scope': getattr(refund, 'refund_scope', ''),
        'completion_state': getattr(refund, 'completion_state', ''),
        'gateway': refund.gateway,
        'provider_reference': refund.provider_reference,
        'amount': float(refund.amount or 0),
        'currency': refund.currency,
        'reason': refund.reason,
        'requested_by_email': refund.requested_by.email if getattr(refund, 'requested_by_id', None) else '',
        'reviewed_by_email': refund.reviewed_by.email if getattr(refund, 'reviewed_by_id', None) else '',
        'requested_at': refund.requested_at,
        'processed_at': refund.processed_at,
        'erpnext_sync_status': getattr(refund, 'erpnext_sync_status', ''),
        'erpnext_reference': getattr(refund, 'erpnext_reference', ''),
        'erpnext_sync_message': getattr(refund, 'erpnext_sync_message', ''),
        'erpnext_synced_at': getattr(refund, 'erpnext_synced_at', None),
        'created_at': refund.created_at,
        'updated_at': refund.updated_at,
    }


def _finance_return_payload(return_case) -> dict:
    return {
        'id': return_case.id,
        'return_reference': return_case.return_reference,
        'payment_reference': return_case.payment_session.reference if return_case.payment_session_id else '',
        'refund_reference': return_case.refund_ledger.refund_reference if return_case.refund_ledger_id else '',
        'order_number': return_case.order.number if return_case.order_id else '',
        'line_id': return_case.line_id,
        'line_title': return_case.line.title if return_case.line_id else '',
        'product_id': return_case.product_id,
        'product_title': return_case.product.title if return_case.product_id else '',
        'stockrecord_id': return_case.stockrecord_id,
        'quantity': return_case.quantity,
        'accepted_quantity': return_case.accepted_quantity,
        'refund_amount': float(return_case.refund_amount or 0),
        'currency': return_case.currency,
        'status': return_case.status,
        'restock_decision': return_case.restock_decision,
        'condition_note': return_case.condition_note,
        'reason': return_case.reason,
        'notes': return_case.notes,
        'erpnext_rule': return_case.erpnext_rule,
        'requested_by_email': return_case.requested_by.email if return_case.requested_by_id else '',
        'reviewed_by_email': return_case.reviewed_by.email if return_case.reviewed_by_id else '',
        'received_at': return_case.received_at,
        'completed_at': return_case.completed_at,
        'restocked_at': return_case.restocked_at,
        'created_at': return_case.created_at,
        'updated_at': return_case.updated_at,
    }


def _finance_order_line_payload(line, payables_by_line: dict) -> dict:
    line_payables = payables_by_line.get(line.id, [])
    supplier_payable_total = sum(Decimal(str(payable.payable_total or 0)) for payable in line_payables)
    gross_margin_total = sum(Decimal(str(getattr(payable.allocation, 'gross_margin', 0) or 0)) for payable in line_payables)
    return {
        'line_id': line.id,
        'product_id': line.product_id,
        'title': line.title,
        'sku': line.partner_sku or '',
        'quantity': line.quantity,
        'line_price_excl_tax': float(line.line_price_excl_tax or 0),
        'line_price_incl_tax': float(line.line_price_incl_tax or 0),
        'supplier_payable_total': float(supplier_payable_total),
        'gross_margin_total': float(gross_margin_total),
        'payables': [_finance_payable_payload(payable) for payable in line_payables],
    }


def _finance_refund_summary(payments) -> dict:
    refund_count = 0
    refund_total = Decimal('0.00')
    requests = []
    payment_ids = [payment.id for payment in payments]
    ledger_refunds = list(
        PaymentRefundLedger.objects.select_related('payment_session', 'order', 'requested_by', 'reviewed_by')
        .filter(payment_session_id__in=payment_ids)
        .order_by('-created_at', '-id')
    )
    for refund in ledger_refunds:
        refund_count += 1
        refund_total += Decimal(str(refund.amount or 0))
        requests.append(_finance_refund_payload(refund))
    payments_with_ledger = {refund.payment_session_id for refund in ledger_refunds}
    for payment in payments:
        if payment.id in payments_with_ledger:
            continue
        for refund in (payment.metadata or {}).get('refund_requests', []):
            refund_count += 1
            amount = Decimal(str(refund.get('amount') or payment.amount or 0))
            refund_total += amount
            requests.append(
                {
                    'id': None,
                    'payment_reference': payment.reference,
                    'order_number': payment.order.number if payment.order_id else '',
                    'refund_reference': refund.get('refund_reference') or '',
                    'refund_type': refund.get('refund_type') or 'refund',
                    'amount': float(amount),
                    'status': refund.get('status') or 'requested',
                    'refund_scope': refund.get('refund_scope') or 'partial',
                    'completion_state': refund.get('completion_state') or 'partial_requested',
                    'gateway': refund.get('gateway') or '',
                    'provider_reference': refund.get('provider_reference') or '',
                    'reason': refund.get('reason') or '',
                    'requested_by_email': '',
                    'reviewed_by_email': '',
                    'requested_at': refund.get('requested_at') or refund.get('created_at') or '',
                    'processed_at': refund.get('processed_at') or '',
                    'erpnext_sync_status': '',
                    'erpnext_reference': '',
                    'erpnext_sync_message': '',
                    'erpnext_synced_at': '',
                    'created_at': refund.get('created_at') or '',
                    'updated_at': refund.get('updated_at') or '',
                }
            )
    return {'count': refund_count, 'total': float(refund_total), 'requests': requests}


def _finance_order_payload(order) -> dict:
    payments = list(order.payment_sessions.all())
    reconciliations = list(order.payment_reconciliations.select_related('payment_session').all())
    payables = list(
        order.supplier_payable_ledgers.select_related(
            'allocation',
            'supplier',
            'supplier__account_manager',
            'partner',
            'line',
            'product',
            'supplier_offer',
            'stockrecord',
        ).all()
    )
    payables_by_line = {}
    for payable in payables:
        payables_by_line.setdefault(payable.line_id, []).append(payable)

    subtotal_excl_tax = Decimal(str(order.total_excl_tax or 0)) - Decimal(str(order.shipping_excl_tax or 0))
    total_paid = sum(Decimal(str(payment.amount or 0)) for payment in payments if payment.status in [PaymentSession.STATUS_AUTHORIZED, PaymentSession.STATUS_PAID])
    supplier_payable_total = sum(Decimal(str(payable.payable_total or 0)) for payable in payables if payable.status != 'reversed')
    gross_margin_total = sum(Decimal(str(getattr(payable.allocation, 'gross_margin', 0) or 0)) for payable in payables)
    gateway_fee_total = sum(Decimal(str(reconciliation.fee_amount or 0)) for reconciliation in reconciliations)
    refund_summary = _finance_refund_summary(payments)
    return_cases = list(
        order.return_cases.select_related(
            'payment_session',
            'refund_ledger',
            'reconciliation',
            'line',
            'product',
            'stockrecord',
            'requested_by',
            'reviewed_by',
        ).all()
    )

    return {
        'id': order.id,
        'number': order.number,
        'status': order.status,
        'currency': order.currency,
        'date_placed': order.date_placed,
        'customer_email': getattr(getattr(order, 'user', None), 'email', '') or order.guest_email or '',
        'shipping_method': order.shipping_method,
        'shipping_code': order.shipping_code,
        'totals': {
            'subtotal_excl_tax': float(subtotal_excl_tax),
            'shipping_excl_tax': float(order.shipping_excl_tax or 0),
            'shipping_incl_tax': float(order.shipping_incl_tax or 0),
            'order_excl_tax': float(order.total_excl_tax or 0),
            'order_incl_tax': float(order.total_incl_tax or 0),
            'paid_total': float(total_paid),
            'supplier_payable_total': float(supplier_payable_total),
            'gross_margin_total': float(gross_margin_total),
            'gateway_fee_total': float(gateway_fee_total),
            'refund_total': float(refund_summary['total']),
            'net_margin_before_overheads': float(gross_margin_total - gateway_fee_total - Decimal(str(refund_summary['total']))),
        },
        'payments': [_finance_payment_payload(payment) for payment in payments],
        'reconciliations': [_finance_reconciliation_payload(reconciliation) for reconciliation in reconciliations],
        'lines': [_finance_order_line_payload(line, payables_by_line) for line in order.lines.select_related('product').all()],
        'supplier_payables': [_finance_payable_payload(payable) for payable in payables],
        'refunds': refund_summary,
        'returns': [_finance_return_payload(return_case) for return_case in return_cases],
    }


class AdminFinanceSummaryAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view finance summary.'}, status=status.HTTP_403_FORBIDDEN)

        SupplierOrderLineAllocation = apps.get_model('marketplace', 'SupplierOrderLineAllocation')
        SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')

        payments = PaymentSession.objects.select_related('order').all()
        reconciliations = PaymentReconciliation.objects.select_related('payment_session', 'order').all()
        payables = SupplierPayableLedger.objects.select_related('supplier', 'partner', 'order', 'line').all()
        allocations = SupplierOrderLineAllocation.objects.all()

        confirmed_payments = payments.filter(status__in=[PaymentSession.STATUS_AUTHORIZED, PaymentSession.STATUS_PAID])
        matched_reconciliations = reconciliations.filter(status=PaymentReconciliation.STATUS_MATCHED)
        unresolved_reconciliations = reconciliations.exclude(
            status__in=[
                PaymentReconciliation.STATUS_MATCHED,
                PaymentReconciliation.STATUS_CANCELLED,
                PaymentReconciliation.STATUS_REFUNDED,
            ]
        )
        active_payables = payables.exclude(status=SupplierPayableLedger.STATUS_REVERSED)
        payable_ready = payables.filter(status__in=[SupplierPayableLedger.STATUS_PAYABLE, SupplierPayableLedger.STATUS_APPROVED])
        supplier_paid = payables.filter(status=SupplierPayableLedger.STATUS_PAID)
        supplier_pending = payables.filter(status=SupplierPayableLedger.STATUS_PENDING)
        fee_total = _money_total(reconciliations, 'fee_amount')
        gross_margin_total = _money_total(allocations, 'gross_margin')
        refund_summary = _refund_request_summary(payments)

        return Response(
            {
                'collections': {
                    'count': confirmed_payments.count(),
                    'total': _money_total(confirmed_payments, 'amount'),
                    'matched_total': _money_total(matched_reconciliations, 'paid_amount'),
                    'by_status': list(payments.values('status').annotate(count=Count('id'), total=Sum('amount')).order_by('status')),
                    'by_method': list(payments.values('method').annotate(count=Count('id'), total=Sum('amount')).order_by('method')),
                },
                'reconciliation': {
                    'total': reconciliations.count(),
                    'unresolved_count': unresolved_reconciliations.count(),
                    'by_status': list(reconciliations.values('status').annotate(count=Count('id')).order_by('status')),
                    'issues_count': reconciliations.exclude(issues=[]).count(),
                },
                'supplier_payables': {
                    'total': _money_total(active_payables, 'payable_total'),
                    'ready_total': _money_total(payable_ready, 'payable_total'),
                    'pending_total': _money_total(supplier_pending, 'payable_total'),
                    'paid_total': _money_total(supplier_paid, 'payable_total'),
                    'by_status': list(payables.values('status').annotate(count=Count('id'), total=Sum('payable_total')).order_by('status')),
                },
                'refunds': refund_summary,
                'fees': {
                    'gateway_fee_total': fee_total,
                },
                'margin': {
                    'gross_margin_total': gross_margin_total,
                    'net_margin_before_overheads': float(Decimal(str(gross_margin_total)) - Decimal(str(fee_total)) - Decimal(str(refund_summary['total']))),
                },
            }
        )


class AdminFinanceReconciliationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view payment reconciliation.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = PaymentReconciliation.objects.select_related('payment_session', 'order').order_by('-updated_at', '-id')
        queryset = _apply_date_filters(queryset, request, field_name='created_at')

        search = (request.query_params.get('q') or '').strip()
        provider = (request.query_params.get('provider') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        currency = (request.query_params.get('currency') or '').strip().upper()
        order_number = (request.query_params.get('order_number') or '').strip()
        reference = (request.query_params.get('reference') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(merchant_reference__icontains=search)
                | Q(provider_reference__icontains=search)
                | Q(payment_session__reference__icontains=search)
                | Q(order__number__icontains=search)
                | Q(payment_session__payer_email__icontains=search)
                | Q(payment_session__payer_phone__icontains=search)
            )
        if provider:
            queryset = queryset.filter(provider=provider)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if currency:
            queryset = queryset.filter(currency=currency)
        if order_number:
            queryset = queryset.filter(order__number__icontains=order_number)
        if reference:
            queryset = queryset.filter(
                Q(merchant_reference__icontains=reference)
                | Q(provider_reference__icontains=reference)
                | Q(payment_session__reference__icontains=reference)
            )

        page_obj, page_size = _page_queryset(request, queryset)
        return Response(
            {
                'results': [_finance_reconciliation_payload(row) for row in page_obj.object_list],
                'pagination': _pagination_payload(page_obj, page_obj.number, page_size),
                'summary': {
                    'count': queryset.count(),
                    'expected_total': _money_total(queryset, 'expected_amount'),
                    'paid_total': _money_total(queryset, 'paid_amount'),
                    'fee_total': _money_total(queryset, 'fee_amount'),
                    'settled_total': _money_total(queryset, 'settled_amount'),
                    'by_status': list(queryset.values('status').annotate(count=Count('id')).order_by('status')),
                },
            }
        )


class AdminFinanceReconciliationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, reconciliation_id: int):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to update payment reconciliation.'}, status=status.HTTP_403_FORBIDDEN)

        reconciliation = get_object_or_404(
            PaymentReconciliation.objects.select_related('payment_session', 'order'),
            id=reconciliation_id,
        )
        serializer = FinanceReconciliationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = reconciliation.status
        new_status = serializer.validated_data['status']
        note = (serializer.validated_data.get('note') or '').strip()
        issues = list(reconciliation.issues or [])
        if note:
            issues.append(f'Manual review by {request.user.email or request.user.username}: {note}')

        reconciliation.status = new_status
        reconciliation.issues = list(dict.fromkeys(issues))
        reconciliation.reviewed_by = request.user
        reconciliation.reviewed_at = timezone.now()
        reconciliation.save(update_fields=['status', 'issues', 'reviewed_by', 'reviewed_at', 'updated_at'])

        log_payment_event(
            reconciliation.payment_session,
            kind=PaymentEvent.KIND_STATUS_APPLIED,
            status_before=old_status,
            status_after=new_status,
            external_reference=reconciliation.provider_reference,
            message=note or 'Payment reconciliation status manually reviewed.',
            payload={
                'reconciliation_id': reconciliation.id,
                'old_status': old_status,
                'new_status': new_status,
                'reviewed_by': request.user.email or request.user.username,
            },
        )
        record_audit_event(
            event_type='finance.reconciliation_status_changed',
            request=request,
            actor=request.user,
            target=reconciliation,
            message='Finance reconciliation status changed.',
            metadata={
                'reconciliation_id': reconciliation.id,
                'payment_reference': reconciliation.payment_session.reference,
                'old_status': old_status,
                'new_status': new_status,
                'note': note,
            },
        )

        return Response({'reconciliation': _finance_reconciliation_payload(reconciliation)})


class AdminFinanceSupplierPayableCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view supplier payables.'}, status=status.HTTP_403_FORBIDDEN)

        SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
        queryset = SupplierPayableLedger.objects.select_related(
            'allocation',
            'supplier',
            'supplier__account_manager',
            'partner',
            'order',
            'line',
            'product',
            'supplier_offer',
            'stockrecord',
        ).order_by('-updated_at', '-id')
        queryset = _apply_date_filters(queryset, request, field_name='created_at')

        search = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        currency = (request.query_params.get('currency') or '').strip().upper()
        supplier_id = (request.query_params.get('supplier_id') or '').strip()
        account_manager_id = (request.query_params.get('account_manager_id') or '').strip()
        order_number = (request.query_params.get('order_number') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(order__number__icontains=search)
                | Q(line__title__icontains=search)
                | Q(product__title__icontains=search)
                | Q(partner__name__icontains=search)
                | Q(supplier__company_name__icontains=search)
                | Q(payout_reference__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if currency:
            queryset = queryset.filter(currency=currency)
        if supplier_id and supplier_id.isdigit():
            queryset = queryset.filter(supplier_id=supplier_id)
        if account_manager_id and account_manager_id.isdigit():
            queryset = queryset.filter(supplier__account_manager_id=account_manager_id)
        if order_number:
            queryset = queryset.filter(order__number__icontains=order_number)

        page_obj, page_size = _page_queryset(request, queryset)
        return Response(
            {
                'results': [_finance_payable_payload(row) for row in page_obj.object_list],
                'pagination': _pagination_payload(page_obj, page_obj.number, page_size),
                'summary': {
                    'count': queryset.count(),
                    'payable_total': _money_total(queryset, 'payable_total'),
                    'gross_margin_total': _money_total(queryset, 'allocation__gross_margin'),
                    'by_status': list(queryset.values('status').annotate(count=Count('id'), total=Sum('payable_total')).order_by('status')),
                },
            }
        )


class AdminFinanceRefundLedgerCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view refund ledger.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = PaymentRefundLedger.objects.select_related(
            'payment_session',
            'reconciliation',
            'order',
            'line',
            'requested_by',
            'reviewed_by',
        ).order_by('-created_at', '-id')
        queryset = _apply_date_filters(queryset, request, field_name='created_at')

        search = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        refund_type = (request.query_params.get('refund_type') or '').strip()
        currency = (request.query_params.get('currency') or '').strip().upper()
        order_number = (request.query_params.get('order_number') or '').strip()
        reference = (request.query_params.get('reference') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(refund_reference__icontains=search)
                | Q(provider_reference__icontains=search)
                | Q(payment_session__reference__icontains=search)
                | Q(order__number__icontains=search)
                | Q(reason__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if refund_type:
            queryset = queryset.filter(refund_type=refund_type)
        if currency:
            queryset = queryset.filter(currency=currency)
        if order_number:
            queryset = queryset.filter(order__number__icontains=order_number)
        if reference:
            queryset = queryset.filter(
                Q(refund_reference__icontains=reference)
                | Q(provider_reference__icontains=reference)
                | Q(payment_session__reference__icontains=reference)
            )

        page_obj, page_size = _page_queryset(request, queryset)
        return Response(
            {
                'results': [_finance_refund_payload(refund) for refund in page_obj.object_list],
                'pagination': _pagination_payload(page_obj, page_obj.number, page_size),
                'summary': {
                    'count': queryset.count(),
                    'total': _money_total(queryset, 'amount'),
                    'by_status': list(queryset.values('status').annotate(count=Count('id'), total=Sum('amount')).order_by('status')),
                    'by_type': list(queryset.values('refund_type').annotate(count=Count('id'), total=Sum('amount')).order_by('refund_type')),
                },
            }
        )


class AdminFinanceReturnCaseCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view return cases.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = PaymentReturnCase.objects.select_related(
            'payment_session',
            'refund_ledger',
            'reconciliation',
            'order',
            'line',
            'product',
            'stockrecord',
            'requested_by',
            'reviewed_by',
        ).order_by('-created_at', '-id')
        queryset = _apply_date_filters(queryset, request, field_name='created_at')

        search = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        restock_decision = (request.query_params.get('restock_decision') or '').strip()
        currency = (request.query_params.get('currency') or '').strip().upper()
        order_number = (request.query_params.get('order_number') or '').strip()
        reference = (request.query_params.get('reference') or '').strip()
        line_id = (request.query_params.get('line_id') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(return_reference__icontains=search)
                | Q(payment_session__reference__icontains=search)
                | Q(refund_ledger__refund_reference__icontains=search)
                | Q(order__number__icontains=search)
                | Q(line__title__icontains=search)
                | Q(reason__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if restock_decision:
            queryset = queryset.filter(restock_decision=restock_decision)
        if currency:
            queryset = queryset.filter(currency=currency)
        if order_number:
            queryset = queryset.filter(order__number__icontains=order_number)
        if reference:
            queryset = queryset.filter(
                Q(return_reference__icontains=reference)
                | Q(payment_session__reference__icontains=reference)
                | Q(refund_ledger__refund_reference__icontains=reference)
            )
        if line_id and line_id.isdigit():
            queryset = queryset.filter(line_id=line_id)

        page_obj, page_size = _page_queryset(request, queryset)
        return Response(
            {
                'results': [_finance_return_payload(return_case) for return_case in page_obj.object_list],
                'pagination': _pagination_payload(page_obj, page_obj.number, page_size),
                'summary': {
                    'count': queryset.count(),
                    'total': _money_total(queryset, 'refund_amount'),
                    'accepted_quantity': queryset.aggregate(total=Sum('accepted_quantity')).get('total') or 0,
                    'by_status': list(queryset.values('status').annotate(count=Count('id'), total=Sum('refund_amount')).order_by('status')),
                    'by_restock_decision': list(queryset.values('restock_decision').annotate(count=Count('id')).order_by('restock_decision')),
                },
            }
        )

    def post(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to create return cases.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FinanceReturnCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = get_payment_or_404(serializer.validated_data['payment_reference'])
        Line = apps.get_model('order', 'Line')
        line = get_object_or_404(Line.objects.select_related('order', 'product', 'stockrecord'), id=serializer.validated_data['line_id'])
        try:
            return_case = create_payment_return_case(
                payment_session=payment,
                line=line,
                quantity=serializer.validated_data['quantity'],
                refund_amount=serializer.validated_data.get('refund_amount'),
                reason=serializer.validated_data.get('reason', ''),
                restock_decision=serializer.validated_data.get('restock_decision', PaymentReturnCase.RESTOCK_PENDING),
                condition_note=serializer.validated_data.get('condition_note', ''),
                notes=serializer.validated_data.get('notes', ''),
                requested_by=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        record_audit_event(
            event_type='finance.return_created',
            request=request,
            actor=request.user,
            target=return_case,
            message='Finance return case created.',
            metadata={'return_reference': return_case.return_reference, 'order_number': return_case.order.number},
        )
        return Response({'return_case': _finance_return_payload(return_case)}, status=status.HTTP_201_CREATED)


class AdminFinanceReturnCaseDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, return_id: int):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view return cases.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'return_case': _finance_return_payload(_get_return_case(return_id))})

    def post(self, request, return_id: int):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to update return cases.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FinanceReturnStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return_case = _get_return_case(return_id)
        try:
            return_case = update_payment_return_case(
                return_case,
                action=serializer.validated_data['action'],
                accepted_quantity=serializer.validated_data.get('accepted_quantity'),
                restock_decision=serializer.validated_data.get('restock_decision', ''),
                condition_note=serializer.validated_data.get('condition_note', ''),
                notes=serializer.validated_data.get('notes', ''),
                reviewed_by=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        record_audit_event(
            event_type='finance.return_status_changed',
            request=request,
            actor=request.user,
            target=return_case,
            message='Finance return case status changed.',
            metadata={'return_reference': return_case.return_reference, 'action': serializer.validated_data['action']},
        )
        return Response({'return_case': _finance_return_payload(_get_return_case(return_case.id))})


class AdminFinanceOrderDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, order_number: str):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view order finance detail.'}, status=status.HTTP_403_FORBIDDEN)

        Order = apps.get_model('order', 'Order')
        queryset = scope_orders_queryset(
            Order.objects.select_related('user', 'shipping_address', 'billing_address')
            .prefetch_related(
                'lines__product',
                'payment_sessions',
                'payment_reconciliations__payment_session',
                'supplier_payable_ledgers__allocation',
                'supplier_payable_ledgers__supplier',
                'supplier_payable_ledgers__supplier__account_manager',
                'supplier_payable_ledgers__partner',
                'supplier_payable_ledgers__line',
                'supplier_payable_ledgers__product',
                'supplier_payable_ledgers__supplier_offer',
                'supplier_payable_ledgers__stockrecord',
                'return_cases__payment_session',
                'return_cases__refund_ledger',
                'return_cases__line',
                'return_cases__product',
                'return_cases__stockrecord',
            ),
            request.user,
        )
        order = get_object_or_404(queryset, number=order_number)
        return Response({'order': _finance_order_payload(order)})


class AdminFinancePayoutBatchCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view payout batches.'}, status=status.HTTP_403_FORBIDDEN)

        SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
        queryset = SupplierPayoutBatch.objects.select_related('supplier', 'partner', 'created_by', 'approved_by', 'paid_by').order_by('-created_at', '-id')
        queryset = _apply_date_filters(queryset, request, field_name='created_at')

        search = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        currency = (request.query_params.get('currency') or '').strip().upper()
        supplier_id = (request.query_params.get('supplier_id') or '').strip()

        if search:
            queryset = queryset.filter(
                Q(batch_reference__icontains=search)
                | Q(payout_reference__icontains=search)
                | Q(supplier__company_name__icontains=search)
                | Q(partner__name__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if currency:
            queryset = queryset.filter(currency=currency)
        if supplier_id and supplier_id.isdigit():
            queryset = queryset.filter(supplier_id=supplier_id)

        page_obj, page_size = _page_queryset(request, queryset)
        return Response(
            {
                'results': [_finance_payout_batch_payload(batch) for batch in page_obj.object_list],
                'pagination': _pagination_payload(page_obj, page_obj.number, page_size),
                'summary': {
                    'count': queryset.count(),
                    'total_amount': _money_total(queryset, 'total_amount'),
                    'by_status': list(queryset.values('status').annotate(count=Count('id'), total=Sum('total_amount')).order_by('status')),
                },
            }
        )

    def post(self, request):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to create payout batches.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = SupplierPayoutBatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch = create_supplier_payout_batch(
                payable_ids=serializer.validated_data['payable_ids'],
                payout_method=serializer.validated_data.get('payout_method', ''),
                notes=serializer.validated_data.get('notes', ''),
                created_by=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'batch': _finance_payout_batch_payload(_get_payout_batch(batch.id), include_entries=True)}, status=status.HTTP_201_CREATED)


class AdminFinancePayoutBatchDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, batch_id: int):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to view payout batches.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'batch': _finance_payout_batch_payload(_get_payout_batch(batch_id), include_entries=True)})


class AdminFinancePayoutBatchStatusAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, batch_id: int, action: str):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to update payout batches.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = SupplierPayoutBatchStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = _get_payout_batch(batch_id)
        try:
            if action == 'submit':
                batch = submit_supplier_payout_batch(batch, user=request.user)
            elif action == 'approve':
                batch = approve_supplier_payout_batch(batch, user=request.user)
            elif action == 'paid':
                batch = mark_supplier_payout_batch_paid(
                    batch,
                    user=request.user,
                    payout_reference=serializer.validated_data.get('payout_reference', ''),
                    evidence_url=serializer.validated_data.get('evidence_url', ''),
                    evidence_file=serializer.validated_data.get('evidence_file'),
                )
                dispatch_background_task(
                    export_supplier_payout_batch_to_erpnext,
                    run_kwargs={'batch_id': batch.id},
                    async_kwargs={'batch_id': batch.id},
                )
            elif action == 'cancel':
                batch = cancel_supplier_payout_batch(batch, user=request.user, reason=serializer.validated_data.get('reason', ''))
            else:
                return Response({'detail': 'Unsupported payout batch action.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'batch': _finance_payout_batch_payload(_get_payout_batch(batch.id), include_entries=True)})


class AdminFinancePayoutBatchCSVAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, batch_id: int):
        if not can_access_finance_data(request.user):
            return Response({'detail': 'Finance access is required to export payout batches.'}, status=status.HTTP_403_FORBIDDEN)
        batch = _get_payout_batch(batch_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Batch Reference', batch.batch_reference])
        writer.writerow(['Supplier', batch.supplier.company_name if batch.supplier_id else batch.partner.name if batch.partner_id else ''])
        writer.writerow(['Status', batch.status])
        writer.writerow(['Currency', batch.currency])
        writer.writerow(['Total Amount', batch.total_amount])
        writer.writerow([])
        writer.writerow(['Payable ID', 'Order Number', 'Product', 'Quantity', 'Amount', 'Currency', 'Payable Status'])
        for entry in batch.entries.select_related('payable', 'payable__order', 'payable__line', 'payable__product').all():
            payable = entry.payable
            writer.writerow([
                payable.id,
                payable.order.number if payable.order_id else '',
                payable.product.title if payable.product_id else payable.line.title,
                payable.quantity,
                entry.amount,
                entry.currency,
                payable.status,
            ])
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{batch.batch_reference}.csv"'
        return response


def _get_payout_batch(batch_id: int):
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    return get_object_or_404(
        SupplierPayoutBatch.objects.select_related('supplier', 'partner', 'created_by', 'approved_by', 'paid_by')
        .prefetch_related(
            'entries__payable',
            'entries__payable__supplier',
            'entries__payable__partner',
            'entries__payable__order',
            'entries__payable__line',
            'entries__payable__product',
        ),
        id=batch_id,
    )


def _get_return_case(return_id: int):
    return get_object_or_404(
        PaymentReturnCase.objects.select_related(
            'payment_session',
            'refund_ledger',
            'reconciliation',
            'order',
            'line',
            'product',
            'stockrecord',
            'requested_by',
            'reviewed_by',
        ),
        id=return_id,
    )


class AdminPaymentSessionLogCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = scope_payment_sessions_queryset(
            PaymentSession.objects.select_related('user', 'order', 'reconciliation')
            .prefetch_related(
                Prefetch(
                    'events',
                    queryset=PaymentEvent.objects.order_by('-created_at', '-id'),
                    to_attr='prefetched_events',
                )
            )
            .order_by('-created_at'),
            request.user,
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

        base_queryset = scope_payment_sessions_queryset(PaymentSession.objects.all(), request.user)
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
        if not can_access_all_admin_data(request.user):
            return Response({'detail': 'Only a platform admin can request refunds.'}, status=status.HTTP_403_FORBIDDEN)
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
        if PaymentRefundLedger.objects.filter(refund_reference=refund_reference).exists() or any(item.get('refund_reference') == refund_reference for item in refund_requests):
            return Response({'detail': 'Refund request already recorded.', 'refund_reference': refund_reference}, status=status.HTTP_200_OK)

        gateway_response = None
        ledger_status = PaymentRefundLedger.STATUS_REQUESTED
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
            ledger_status = PaymentRefundLedger.STATUS_SUBMITTED
            log_payment_event(
                payment,
                kind='provider_submitted',
                status_before=payment.status,
                status_after=payment.status,
                external_reference=payment.external_reference,
                message='Pesapal refund request submitted.',
                payload={'phase': 'pesapal_refund_request', 'refund_reference': refund_reference, 'pesapal_response': gateway_response},
            )

        refund_ledger = record_payment_refund_ledger(
            payment,
            amount=refund_amount,
            reason=reason,
            refund_reference=refund_reference,
            refund_type=PaymentRefundLedger.TYPE_REFUND,
            status=ledger_status,
            gateway=payment.method if submit_gateway_refund else 'manual',
            provider_reference=str((gateway_response or {}).get('refund_request_id') or (gateway_response or {}).get('order_tracking_id') or ''),
            gateway_payload=gateway_response or {},
            requested_by=request.user,
        )
        supplier_adjustments = create_supplier_debit_adjustments_for_refund(refund_ledger, created_by=request.user)

        refund_requests.append(
            {
                'refund_reference': refund_reference,
                'amount': str(refund_amount),
                'reason': reason,
                'status': refund_ledger.status,
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
            metadata={
                'payment_reference': payment.reference,
                'refund_reference': refund_reference,
                'refund_ledger_id': refund_ledger.id,
                'supplier_adjustment_count': len(supplier_adjustments),
                'amount': str(refund_amount),
            },
        )
        return Response(
            {
                'detail': 'Refund accounting export queued.',
                'refund_reference': refund_reference,
                'refund': _finance_refund_payload(refund_ledger),
                'supplier_adjustment_count': len(supplier_adjustments),
            },
            status=status.HTTP_202_ACCEPTED,
        )


def _order_has_cash_on_delivery(order) -> bool:
    return PaymentSession.objects.filter(order=order, method=PaymentSession.METHOD_CASH_ON_DELIVERY).exists()


def _order_paid_amount(order) -> Decimal:
    total = (
        PaymentSession.objects.filter(
            order=order,
            status__in=[PaymentSession.STATUS_AUTHORIZED, PaymentSession.STATUS_PAID],
        )
        .exclude(method=PaymentSession.METHOD_CASH_ON_DELIVERY)
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )
    return Decimal(str(total)).quantize(Decimal('0.01'))


def _order_phone(order) -> str:
    address = getattr(order, 'shipping_address', None)
    for field in ('phone_number', 'phone'):
        value = (getattr(address, field, '') or '').strip() if address else ''
        if value:
            return value
    user = getattr(order, 'user', None)
    profile = getattr(user, 'customer_profile', None)
    return (getattr(profile, 'phone', '') or '').strip()


class AdminCodMpesaPromptAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, order_number: str):
        order = get_object_or_404(scope_orders_queryset(apps.get_model('order', 'Order').objects.all(), request.user), number=order_number)
        serializer = AdminCodMpesaPromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not _order_has_cash_on_delivery(order):
            return Response({'detail': 'This order was not placed with Cash on Delivery.'}, status=status.HTTP_400_BAD_REQUEST)
        if not mpesa_is_configured():
            return Response(
                {
                    'error': {
                        'code': 'mpesa_not_configured',
                        'detail': 'M-Pesa Daraja credentials are not configured.',
                        'status': status.HTTP_503_SERVICE_UNAVAILABLE,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        order_total = Decimal(str(order.total_incl_tax or 0)).quantize(Decimal('0.01'))
        outstanding = (order_total - _order_paid_amount(order)).quantize(Decimal('0.01'))
        amount = Decimal(str(serializer.validated_data.get('amount') or outstanding)).quantize(Decimal('0.01'))
        if outstanding <= Decimal('0.00'):
            return Response({'detail': 'This order already has confirmed payment covering the total.'}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= Decimal('0.00') or amount > outstanding:
            return Response({'detail': 'Prompt amount must be greater than zero and not exceed the outstanding balance.'}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = (serializer.validated_data.get('phone_number') or _order_phone(order)).strip()
        if not phone_number:
            return Response({'detail': 'A customer phone number is required to send an M-Pesa prompt.'}, status=status.HTTP_400_BAD_REQUEST)

        payment_session = initialize_payment_session(
            basket=None,
            user=order.user,
            method_code=PaymentSession.METHOD_MPESA,
            amount=amount,
            currency=order.currency,
            payer_email=getattr(order.user, 'email', '') if order.user_id else getattr(order, 'guest_email', ''),
            payer_phone=phone_number,
            metadata={
                'source': 'cod_dispatch_prompt',
                'order_number': order.number,
                'triggered_by_user_id': request.user.id,
                'outstanding_before_prompt': str(outstanding),
            },
        )
        payment_session.order = order
        payment_session.save(update_fields=['order', 'updated_at'])

        try:
            provider_payload = initiate_stk_push(payment_session)
        except (MpesaConfigurationError, MpesaGatewayError) as exc:
            payment_session.status = PaymentSession.STATUS_FAILED
            payment_session.metadata = {**payment_session.metadata, 'gateway_error': str(exc)}
            payment_session.save(update_fields=['status', 'metadata', 'updated_at'])
            return Response(
                {
                    'error': {
                        'code': 'mpesa_gateway_error',
                        'detail': str(exc),
                        'status': status.HTTP_502_BAD_GATEWAY,
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        log_payment_event(
            payment_session,
            kind='provider_submitted',
            status_before=PaymentSession.STATUS_INITIALIZED,
            status_after=payment_session.status,
            external_reference=payment_session.external_reference,
            message='Staff prompted M-Pesa payment for a COD order before dispatch.',
            payload={'provider_payload': provider_payload, 'order_number': order.number},
        )
        record_audit_event(
            event_type='payments.cod_mpesa_prompted',
            request=request,
            actor=request.user,
            target=order,
            message='Staff prompted M-Pesa Express payment for COD order.',
            metadata={'order_number': order.number, 'payment_reference': payment_session.reference, 'amount': str(amount)},
        )

        payload = serialize_payment_session(payment_session)
        payload['provider_payload'] = provider_payload
        return Response({'detail': 'M-Pesa prompt sent.', 'payment': payload}, status=status.HTTP_201_CREATED)


def get_payment_or_404(reference: str):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(PaymentSession.objects.select_related('order'), reference=reference)
