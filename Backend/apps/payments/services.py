from decimal import Decimal
from datetime import timedelta
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.utils import timezone

from .config import provider_is_configured, provider_is_enabled


OFFLINE_PAYMENT_PROVIDERS = {'bank_transfer', 'cash_on_delivery'}
SUCCESS_PAYMENT_STATUSES = {'authorized', 'paid'}
PAYMENT_ATTENTION_SEVERITIES = {'critical', 'error'}


def available_payment_methods() -> list[dict]:
    methods = []
    for method in settings.PAYMENT_METHODS:
        provider = method.get('provider') or method.get('code')
        if _payment_method_is_available(provider):
            payload = method.copy()
            payload['is_configured'] = provider_is_configured(provider)
            methods.append(payload)
    return methods


def get_payment_method(code: str) -> dict | None:
    normalized = (code or '').strip()
    for method in settings.PAYMENT_METHODS:
        if method['code'] == normalized:
            provider = method.get('provider') or method.get('code')
            if not _payment_method_is_available(provider):
                return None
            payload = method.copy()
            payload['is_configured'] = provider_is_configured(provider)
            return payload
    return None


def _payment_method_is_available(provider: str) -> bool:
    if not provider_is_enabled(provider, default=True):
        return False
    if provider in OFFLINE_PAYMENT_PROVIDERS:
        return True
    return provider_is_configured(provider)


def payment_requires_prepayment(method_code: str) -> bool:
    method = get_payment_method(method_code)
    return bool(method and method.get('requires_prepayment'))


def generate_payment_reference(prefix: str = 'PAY') -> str:
    return f'{prefix}-{uuid4().hex[:12].upper()}'


def initialize_payment_session(
    *,
    basket,
    user,
    method_code: str,
    amount,
    currency: str,
    payer_email: str = '',
    payer_phone: str = '',
    metadata: dict | None = None,
    status: str | None = None,
    provider_payload: dict | None = None,
):
    PaymentSession = apps.get_model('payments', 'PaymentSession')

    method = get_payment_method(method_code)
    if method is None:
        raise ValueError('Unsupported payment method.')

    provider = method['provider']
    reference = generate_payment_reference()
    amount = Decimal(str(amount)).quantize(Decimal('0.01'))
    session = PaymentSession.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        basket=basket,
        method=method_code,
        status=status or _initial_status_for_method(method_code),
        provider=provider,
        reference=reference,
        amount=amount,
        currency=currency,
        payer_email=payer_email,
        payer_phone=payer_phone,
        metadata=metadata or {},
        provider_payload=provider_payload or _initial_provider_payload(method_code, reference, amount, currency),
    )
    log_payment_event(
        session,
        kind='initialized',
        status_after=session.status,
        external_reference=session.external_reference,
        payload={
            'method': method_code,
            'provider': provider,
            'amount': str(amount),
            'currency': currency,
            'basket_id': getattr(basket, 'id', None),
        },
    )
    return session


def confirm_payment_session(payment_session, *, success: bool, external_reference: str = '', metadata: dict | None = None):
    previous_status = payment_session.status
    next_status = _success_status_for_method(payment_session.method) if success else payment_session.STATUS_FAILED

    if previous_status in SUCCESS_PAYMENT_STATUSES or previous_status == next_status:
        payment_session.external_reference = external_reference or payment_session.external_reference
        if metadata:
            payment_session.metadata = {**payment_session.metadata, **metadata}
            payment_session.save(update_fields=['external_reference', 'metadata', 'updated_at'])
        elif external_reference:
            payment_session.save(update_fields=['external_reference', 'updated_at'])
        log_payment_event(
            payment_session,
            kind='status_ignored',
            status_before=previous_status,
            status_after=payment_session.status,
            external_reference=payment_session.external_reference,
            message='Ignored duplicate terminal payment update.',
            payload={'requested_success': success, 'requested_status': next_status, 'metadata': metadata or {}},
        )
        return payment_session

    payment_session.external_reference = external_reference or payment_session.external_reference
    merged_metadata = payment_session.metadata.copy()
    if metadata:
        merged_metadata.update(metadata)
    payment_session.metadata = merged_metadata
    if success:
        payment_session.status = next_status
        payment_session.paid_at = timezone.now()
    else:
        payment_session.status = next_status
    payment_session.save(update_fields=['external_reference', 'metadata', 'status', 'paid_at', 'updated_at'])
    log_payment_event(
        payment_session,
        kind='status_applied',
        status_before=previous_status,
        status_after=payment_session.status,
        external_reference=payment_session.external_reference,
        payload={'success': success, 'metadata': metadata or {}},
    )
    return payment_session


def link_payment_to_order(payment_session, order):
    if payment_session.order_id == order.id:
        return None

    payment_session.order = order
    payment_session.save(update_fields=['order', 'updated_at'])

    SourceType = apps.get_model('payment', 'SourceType')
    Source = apps.get_model('payment', 'Source')
    Transaction = apps.get_model('payment', 'Transaction')

    source_type, _ = SourceType.objects.get_or_create(
        code=payment_session.method,
        defaults={'name': get_payment_method(payment_session.method)['name']},
    )

    amount_allocated = payment_session.amount if payment_session.status in {'authorized', 'paid'} else Decimal('0.00')
    amount_debited = payment_session.amount if payment_session.status == 'paid' else Decimal('0.00')

    source = Source.objects.create(
        order=order,
        source_type=source_type,
        currency=payment_session.currency,
        amount_allocated=amount_allocated,
        amount_debited=amount_debited,
        reference=payment_session.reference,
        label=source_type.name,
    )

    txn_type = 'Debit' if payment_session.status == 'paid' else 'Authorize'
    Transaction.objects.create(
        source=source,
        txn_type=txn_type,
        amount=payment_session.amount,
        reference=payment_session.external_reference or payment_session.reference,
        status=payment_session.status,
    )
    log_payment_event(
        payment_session,
        kind='order_linked',
        status_before=payment_session.status,
        status_after=payment_session.status,
        external_reference=payment_session.external_reference,
        payload={'order_id': order.id, 'order_number': order.number},
    )

    return source


def payment_reconciliation(payment_session, *, now=None) -> dict:
    now = now or timezone.now()
    issues = []
    status = 'ok'
    severity = 'ok'
    order = getattr(payment_session, 'order', None)
    is_success = payment_session.status in SUCCESS_PAYMENT_STATUSES

    if is_success and not payment_session.order_id:
        status = 'paid_no_order'
        severity = 'critical'
        issues.append('Payment is confirmed but no order is linked.')
    elif payment_session.status in {payment_session.STATUS_FAILED, payment_session.STATUS_CANCELLED} and payment_session.order_id:
        status = 'failed_linked_order'
        severity = 'critical'
        issues.append('A failed or cancelled payment is linked to an order.')
    elif payment_session.status == payment_session.STATUS_PENDING and payment_session.created_at:
        if payment_session.created_at <= now - timedelta(minutes=30):
            status = 'pending_too_long'
            severity = 'warning'
            issues.append('Payment has been pending for more than 30 minutes.')

    if order and is_success:
        order_currency = getattr(order, 'currency', '') or ''
        order_total = getattr(order, 'total_incl_tax', None)
        if order_currency and payment_session.currency and order_currency != payment_session.currency:
            status = 'order_mismatch'
            severity = 'critical'
            issues.append(f'Order currency {order_currency} does not match payment currency {payment_session.currency}.')
        if order_total is not None:
            payment_amount = Decimal(str(payment_session.amount)).quantize(Decimal('0.01'))
            order_amount = Decimal(str(order_total)).quantize(Decimal('0.01'))
            if payment_amount != order_amount:
                status = 'order_mismatch'
                severity = 'critical'
                issues.append(f'Order total {order_amount} does not match payment amount {payment_amount}.')

    if not issues:
        if payment_session.status == payment_session.STATUS_PENDING:
            status = 'pending'
            severity = 'warning'
        elif is_success and payment_session.order_id:
            status = 'matched'
            severity = 'ok'
        elif payment_session.status in {payment_session.STATUS_FAILED, payment_session.STATUS_CANCELLED}:
            status = payment_session.status
            severity = 'error'
        else:
            status = payment_session.status or 'unknown'
            severity = 'info'

    labels = {
        'matched': 'Matched',
        'paid_no_order': 'Paid, no order',
        'failed_linked_order': 'Failed, linked order',
        'order_mismatch': 'Order mismatch',
        'pending_too_long': 'Pending too long',
        'pending': 'Pending',
        'failed': 'Failed',
        'cancelled': 'Cancelled',
        'authorized': 'Authorized',
        'paid': 'Paid',
        'ok': 'OK',
    }
    return {
        'status': status,
        'label': labels.get(status, status.replace('_', ' ').title()),
        'severity': severity,
        'issues': issues,
        'needs_attention': severity in PAYMENT_ATTENTION_SEVERITIES,
    }


def log_payment_event(
    payment_session,
    *,
    kind: str,
    status_before: str = '',
    status_after: str = '',
    external_reference: str = '',
    message: str = '',
    payload: dict | None = None,
):
    PaymentEvent = apps.get_model('payments', 'PaymentEvent')
    return PaymentEvent.objects.create(
        payment_session=payment_session,
        kind=kind,
        status_before=status_before or '',
        status_after=status_after or '',
        external_reference=external_reference or '',
        message=message or '',
        payload=payload or {},
    )


def serialize_payment_session(payment_session) -> dict:
    method = get_payment_method(payment_session.method) or {}
    return {
        'id': payment_session.id,
        'reference': payment_session.reference,
        'method': payment_session.method,
        'method_name': method.get('name', payment_session.method),
        'provider': payment_session.provider,
        'status': payment_session.status,
        'amount': float(payment_session.amount),
        'currency': payment_session.currency,
        'payer_email': payment_session.payer_email,
        'payer_phone': payment_session.payer_phone,
        'external_reference': payment_session.external_reference,
        'metadata': payment_session.metadata,
        'provider_payload': payment_session.provider_payload,
        'order_number': payment_session.order.number if payment_session.order_id else '',
        'created_at': payment_session.created_at,
        'updated_at': payment_session.updated_at,
        'paid_at': payment_session.paid_at,
    }


def _initial_status_for_method(method_code: str) -> str:
    if method_code in {'bank_transfer', 'cash_on_delivery'}:
        return 'authorized'
    return 'pending'


def _success_status_for_method(method_code: str) -> str:
    if method_code in {'credit_card', 'debit_card', 'cash_on_delivery', 'bank_transfer'}:
        return 'authorized'
    return 'paid'


def _initial_provider_payload(method_code: str, reference: str, amount: Decimal, currency: str) -> dict:
    if method_code == 'mpesa':
        return {
            'channel': 'stk_push',
            'instructions': 'Trigger M-Pesa STK push on the customer handset, then confirm via callback.',
            'reference': reference,
            'amount': float(amount),
            'currency': currency,
        }
    if method_code == 'airtel_money':
        return {
            'channel': 'ussd_push',
            'instructions': 'Trigger Airtel Money collection request, then confirm via callback.',
            'reference': reference,
            'amount': float(amount),
            'currency': currency,
        }
    if method_code in {'credit_card', 'debit_card'}:
        return {
            'channel': 'card_tokenization',
            'instructions': 'Collect card details on the PCI-compliant frontend and exchange for a provider token.',
            'reference': reference,
            'amount': float(amount),
            'currency': currency,
        }
    if method_code == 'bank_transfer':
        return {
            'channel': 'manual_bank_transfer',
            'instructions': 'Display bank transfer instructions and wait for manual reconciliation.',
            'reference': reference,
            'amount': float(amount),
            'currency': currency,
        }
    return {
        'channel': 'offline_collection',
        'instructions': 'Collect payment on delivery and confirm after dispatch.',
        'reference': reference,
        'amount': float(amount),
        'currency': currency,
    }
