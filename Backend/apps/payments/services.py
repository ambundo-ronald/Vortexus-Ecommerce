import logging
from decimal import Decimal
from datetime import timedelta
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .config import get_payment_setting, provider_is_configured, provider_is_enabled


logger = logging.getLogger(__name__)
OFFLINE_PAYMENT_PROVIDERS = {'bank_transfer', 'cash_on_delivery'}
SUCCESS_PAYMENT_STATUSES = {'authorized', 'paid'}
PAYMENT_ATTENTION_SEVERITIES = {'critical', 'error'}
FULFILLMENT_BLOCKING_RECONCILIATION_STATUSES = {
    'pending',
    'amount_mismatch',
    'duplicate',
    'failed',
    'cancelled',
    'reversed',
    'refunded',
    'manual_review',
}
CANCELLATION_REFUND_ORDER_STATUSES = {'cancelled', 'canceled'}
FULFILLED_LINE_STATUSES = {'shipped', 'delivered'}


def customer_can_use_cash_on_delivery(user, basket=None) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_staff', False):
        return True
    if not bool(get_payment_setting('cash_on_delivery', 'requires_customer_approval', True)):
        return True
    profile = getattr(user, 'customer_profile', None)
    return bool(profile and profile.cash_on_delivery_allowed)


def customer_can_use_bank_transfer(user, basket=None) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_staff', False):
        return True
    if not bool(get_payment_setting('bank_transfer', 'requires_customer_approval', True)):
        return True
    profile = getattr(user, 'customer_profile', None)
    return bool(profile and profile.bank_transfer_allowed)


def cash_on_delivery_state(user, basket=None) -> dict:
    requires_customer_approval = bool(get_payment_setting('cash_on_delivery', 'requires_customer_approval', True))
    customer_approved = customer_can_use_cash_on_delivery(user, basket)
    provider_available = _payment_method_is_available('cash_on_delivery')
    return {
        'requires_customer_approval': requires_customer_approval,
        'customer_approved': customer_approved,
        'provider_available': provider_available,
        'available': bool(provider_available and customer_approved),
    }


def bank_transfer_state(user, basket=None) -> dict:
    requires_customer_approval = bool(get_payment_setting('bank_transfer', 'requires_customer_approval', True))
    customer_approved = customer_can_use_bank_transfer(user, basket)
    provider_available = _payment_method_is_available('bank_transfer')
    return {
        'requires_customer_approval': requires_customer_approval,
        'customer_approved': customer_approved,
        'provider_available': provider_available,
        'available': bool(provider_available and customer_approved),
    }


def available_payment_methods(*, user=None, basket=None) -> list[dict]:
    methods = []
    for method in settings.PAYMENT_METHODS:
        is_cash_on_delivery = method.get('code') == 'cash_on_delivery'
        is_bank_transfer = method.get('code') == 'bank_transfer'
        cod_state = cash_on_delivery_state(user, basket) if is_cash_on_delivery else None
        bank_state = bank_transfer_state(user, basket) if is_bank_transfer else None
        if is_cash_on_delivery and not cod_state['available']:
            continue
        if is_bank_transfer and not bank_state['available']:
            continue
        provider = method.get('provider') or method.get('code')
        if _payment_method_is_available(provider):
            payload = method.copy()
            payload['is_configured'] = provider_is_configured(provider)
            payload.update(_payment_method_capabilities(method['code'], provider))
            if cod_state:
                payload['cash_on_delivery'] = cod_state
            if bank_state:
                payload['bank_transfer'] = bank_state
            methods.append(payload)
    return methods


def get_payment_method(code: str, *, user=None, basket=None) -> dict | None:
    normalized = (code or '').strip()
    for method in settings.PAYMENT_METHODS:
        if method['code'] == normalized:
            is_cash_on_delivery = method.get('code') == 'cash_on_delivery'
            is_bank_transfer = method.get('code') == 'bank_transfer'
            cod_state = cash_on_delivery_state(user, basket) if is_cash_on_delivery else None
            bank_state = bank_transfer_state(user, basket) if is_bank_transfer else None
            if is_cash_on_delivery and not cod_state['available']:
                return None
            if is_bank_transfer and not bank_state['available']:
                return None
            provider = method.get('provider') or method.get('code')
            if not _payment_method_is_available(provider):
                return None
            payload = method.copy()
            payload['is_configured'] = provider_is_configured(provider)
            payload.update(_payment_method_capabilities(method['code'], provider))
            if cod_state:
                payload['cash_on_delivery'] = cod_state
            if bank_state:
                payload['bank_transfer'] = bank_state
            return payload
    return None


def payment_method_definition(code: str) -> dict | None:
    normalized = (code or '').strip()
    for method in settings.PAYMENT_METHODS:
        if method['code'] == normalized:
            return method.copy()
    return None


def _payment_method_is_available(provider: str) -> bool:
    default_enabled = provider not in {'cash_on_delivery', 'bank_transfer'}
    if not provider_is_enabled(provider, default=default_enabled):
        return False
    if provider in OFFLINE_PAYMENT_PROVIDERS:
        return True
    return provider_is_configured(provider)


def _payment_method_capabilities(method_code: str, provider: str) -> dict:
    if method_code == 'pesapal':
        base_url = str(get_payment_setting('pesapal', 'base_url', settings.PESAPAL_BASE_URL)).lower()
        return {
            'flow': 'redirect',
            'is_sandbox': 'cybqa' in base_url or 'sandbox' in base_url,
        }
    if method_code == 'mpesa':
        base_url = str(get_payment_setting('mpesa', 'base_url', settings.MPESA_BASE_URL)).lower()
        return {
            'flow': 'mobile_prompt',
            'is_sandbox': 'sandbox' in base_url,
        }
    if method_code == 'airtel_money':
        return {
            'flow': 'mobile_prompt',
            'is_sandbox': bool(settings.AIRTEL_MONEY_SANDBOX_ENABLED),
        }
    if provider == 'card':
        return {
            'flow': 'card_token',
            'is_sandbox': bool(settings.CARD_SANDBOX_ENABLED),
        }
    return {
        'flow': 'offline',
        'is_sandbox': False,
    }


def payment_requires_prepayment(method_code: str, *, user=None, basket=None) -> bool:
    method = get_payment_method(method_code, user=user, basket=basket)
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

    method = get_payment_method(method_code, user=user, basket=basket)
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
    sync_payment_reconciliation(session)
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
        if payment_session.status in SUCCESS_PAYMENT_STATUSES and payment_session.order_id:
            _post_payment_accounting(payment_session)
            _queue_paid_order_accounting_export(payment_session)
        sync_payment_reconciliation(payment_session)
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
    _notify_admin_payment_status(payment_session, previous_status=previous_status)
    sync_payment_reconciliation(payment_session)
    if payment_session.status in SUCCESS_PAYMENT_STATUSES and payment_session.order_id:
        _post_payment_accounting(payment_session)
        _queue_paid_order_accounting_export(payment_session)
    elif payment_session.status == payment_session.STATUS_FAILED and payment_session.order_id:
        handle_failed_payment_linked_order(payment_session)
    return payment_session


@transaction.atomic
def handle_failed_payment_linked_order(payment_session):
    if not payment_session.order_id:
        return None

    order = payment_session.order
    if _order_has_fulfilled_lines(order):
        sync_payment_reconciliation(payment_session)
        return order

    previous_status = order.status or ''
    if previous_status.strip().lower() not in {'failed', 'cancelled', 'canceled'}:
        OrderStatusChange = apps.get_model('order', 'OrderStatusChange')
        OrderStatusChange.objects.create(order=order, old_status=previous_status, new_status='Failed')
        order.status = 'Failed'
        order.save(update_fields=['status'])

    _cancel_unfulfilled_line_allocations(order)
    try:
        from apps.marketplace.payables import sync_supplier_payables_for_order

        sync_supplier_payables_for_order(order)
    except Exception:
        pass
    sync_payment_reconciliation(payment_session)
    return order


@transaction.atomic
def cancel_unpaid_order_finance(order, *, reason: str = '', user=None):
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    sessions = PaymentSession.objects.select_for_update().filter(order=order).exclude(status__in=SUCCESS_PAYMENT_STATUSES)
    for session in sessions:
        if session.status != PaymentSession.STATUS_CANCELLED:
            previous_status = session.status
            session.status = PaymentSession.STATUS_CANCELLED
            metadata = session.metadata or {}
            session.metadata = {
                **metadata,
                'cancelled_reason': reason or 'Order cancelled before payment.',
                'cancelled_by_user_id': getattr(user, 'id', None),
                'cancelled_at': timezone.now().isoformat(),
            }
            session.save(update_fields=['status', 'metadata', 'updated_at'])
            log_payment_event(
                session,
                kind='status_applied',
                status_before=previous_status,
                status_after=session.status,
                message='Payment session cancelled because the unpaid order was cancelled.',
                payload={'reason': reason or ''},
            )
            sync_payment_reconciliation(session)

    _cancel_unfulfilled_line_allocations(order)
    from apps.marketplace.payables import sync_supplier_payables_for_order

    return sync_supplier_payables_for_order(order)


@transaction.atomic
def record_paid_order_cancellation_finance(order, *, reason: str = '', user=None):
    if _order_has_fulfilled_lines(order):
        raise ValueError('This order has shipped or delivered lines. Use the return intake workflow after fulfillment.')

    payment_session = _latest_successful_payment_for_order(order)
    if not payment_session:
        return cancel_unpaid_order_finance(order, reason=reason, user=user)

    refund_reference = f'CANCEL-{order.number}'
    refund_ledger = record_payment_refund_ledger(
        payment_session,
        amount=payment_session.amount,
        reason=reason or 'Order cancelled before fulfillment.',
        refund_reference=refund_reference,
        refund_type=apps.get_model('payments', 'PaymentRefundLedger').TYPE_CANCELLATION,
        status=apps.get_model('payments', 'PaymentRefundLedger').STATUS_REQUESTED,
        gateway='cancellation',
        requested_by=user,
        notes='Paid order cancelled before fulfillment; supplier payable reversed if unpaid.',
    )
    _cancel_unfulfilled_line_allocations(order)

    from apps.marketplace.payables import create_supplier_debit_adjustments_for_refund, sync_supplier_payables_for_order

    sync_supplier_payables_for_order(order)
    create_supplier_debit_adjustments_for_refund(refund_ledger, created_by=user)
    _queue_refund_credit_note_export(refund_ledger)
    return refund_ledger


def ensure_order_finance_clear_for_fulfillment(order):
    payment_session = _latest_successful_payment_for_order(order)
    if not payment_session:
        raise ValueError('Order cannot move into fulfillment until payment is confirmed.')

    reconciliation = sync_payment_reconciliation(payment_session)
    if reconciliation.status in FULFILLMENT_BLOCKING_RECONCILIATION_STATUSES:
        issue = '; '.join(reconciliation.issues or []) or f'Reconciliation status is {reconciliation.status}.'
        raise ValueError(f'Order cannot move into fulfillment until payment reconciliation is clear: {issue}')
    return reconciliation


def ensure_order_finance_clear_for_payout(order):
    payment_session = _latest_successful_payment_for_order(order)
    if not payment_session:
        raise ValueError(f'Order {getattr(order, "number", "")} has no confirmed payment.')

    reconciliation = sync_payment_reconciliation(payment_session)
    if reconciliation.status != apps.get_model('payments', 'PaymentReconciliation').STATUS_MATCHED:
        issue = '; '.join(reconciliation.issues or []) or f'Reconciliation status is {reconciliation.status}.'
        raise ValueError(f'Order {getattr(order, "number", "")} is not payout-safe: {issue}')
    return reconciliation


def order_has_fulfilled_lines(order) -> bool:
    return _order_has_fulfilled_lines(order)


def link_payment_to_order(payment_session, order):
    if payment_session.order_id == order.id:
        sync_payment_reconciliation(payment_session)
        return None

    payment_session.order = order
    payment_session.save(update_fields=['order', 'updated_at'])

    SourceType = apps.get_model('payment', 'SourceType')
    Source = apps.get_model('payment', 'Source')
    Transaction = apps.get_model('payment', 'Transaction')

    method_definition = payment_method_definition(payment_session.method) or {'name': payment_session.method}
    source_type, _ = SourceType.objects.get_or_create(
        code=payment_session.method,
        defaults={'name': method_definition['name']},
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
    if payment_session.status in SUCCESS_PAYMENT_STATUSES:
        _notify_admin_paid_order(payment_session)
        _post_payment_accounting(payment_session)
        _queue_paid_order_accounting_export(payment_session)

    sync_payment_reconciliation(payment_session)
    return source


def _latest_successful_payment_for_order(order):
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    return (
        PaymentSession.objects.filter(order=order, status__in=SUCCESS_PAYMENT_STATUSES)
        .order_by('-paid_at', '-updated_at', '-created_at')
        .first()
    )


def _order_has_fulfilled_lines(order) -> bool:
    return order.lines.filter(status__in=FULFILLED_LINE_STATUSES).exists()


def _cancel_unfulfilled_line_allocations(order) -> None:
    for line in order.lines.all():
        line_status = str(line.status or '').strip().lower()
        if line_status in FULFILLED_LINE_STATUSES:
            continue
        if line_status not in {'cancelled', 'canceled'}:
            line.status = 'cancelled'
            line.save(update_fields=['status'])
        if getattr(line, 'num_allocated', 0):
            line.cancel_allocation(line.num_allocated)


def sync_payment_reconciliation(payment_session):
    PaymentReconciliation = apps.get_model('payments', 'PaymentReconciliation')
    payment_session.refresh_from_db(fields=[
        'order',
        'status',
        'amount',
        'currency',
        'external_reference',
        'provider_payload',
        'metadata',
        'updated_at',
    ])
    snapshot = payment_reconciliation(payment_session)
    reconciliation_status = _ledger_status_for_payment(payment_session, snapshot)
    fee_amount = _money_from_metadata(payment_session.metadata, 'fee_amount')
    paid_amount = payment_session.amount if payment_session.status in SUCCESS_PAYMENT_STATUSES else Decimal('0.00')
    settled_amount = max(paid_amount - fee_amount, Decimal('0.00'))
    payload = {
        'order': payment_session.order,
        'provider': payment_session.provider,
        'method': payment_session.method,
        'merchant_reference': payment_session.reference,
        'provider_reference': payment_session.external_reference or '',
        'expected_amount': payment_session.amount,
        'paid_amount': paid_amount,
        'fee_amount': fee_amount,
        'settled_amount': settled_amount,
        'currency': payment_session.currency,
        'status': reconciliation_status,
        'issues': snapshot.get('issues') or [],
        'raw_provider_payload': {
            'provider_payload': payment_session.provider_payload or {},
            'metadata': payment_session.metadata or {},
        },
        'last_checked_at': timezone.now(),
    }
    reconciliation, _ = PaymentReconciliation.objects.update_or_create(
        payment_session=payment_session,
        defaults=payload,
    )
    return reconciliation


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


def _ledger_status_for_payment(payment_session, snapshot: dict) -> str:
    PaymentReconciliation = apps.get_model('payments', 'PaymentReconciliation')
    provider_reference = (payment_session.external_reference or '').strip()
    if provider_reference:
        duplicate_exists = (
            type(payment_session).objects.filter(
                provider=payment_session.provider,
                external_reference=provider_reference,
                status__in=SUCCESS_PAYMENT_STATUSES,
            )
            .exclude(id=payment_session.id)
            .exists()
        )
        if duplicate_exists:
            return PaymentReconciliation.STATUS_DUPLICATE

    snapshot_status = snapshot.get('status')
    if snapshot_status == 'matched':
        return PaymentReconciliation.STATUS_MATCHED
    if snapshot_status == 'order_mismatch':
        return PaymentReconciliation.STATUS_AMOUNT_MISMATCH
    if snapshot_status in {'paid_no_order', 'failed_linked_order'}:
        return PaymentReconciliation.STATUS_MANUAL_REVIEW
    if payment_session.status == payment_session.STATUS_FAILED:
        return PaymentReconciliation.STATUS_FAILED
    if payment_session.status == payment_session.STATUS_CANCELLED:
        return PaymentReconciliation.STATUS_CANCELLED
    return PaymentReconciliation.STATUS_PENDING


def _money_from_metadata(metadata: dict | None, key: str) -> Decimal:
    try:
        return Decimal(str((metadata or {}).get(key) or '0')).quantize(Decimal('0.01'))
    except (ArithmeticError, TypeError, ValueError):
        return Decimal('0.00')


def _money(value) -> Decimal:
    try:
        return Decimal(str(value or '0')).quantize(Decimal('0.01'))
    except (ArithmeticError, TypeError, ValueError):
        return Decimal('0.00')


@transaction.atomic
def record_payment_refund_ledger(
    payment_session,
    *,
    amount,
    reason: str = '',
    refund_reference: str = '',
    refund_type: str = 'refund',
    status: str = 'requested',
    gateway: str = '',
    provider_reference: str = '',
    gateway_payload: dict | None = None,
    requested_by=None,
    reviewed_by=None,
    line=None,
    notes: str = '',
):
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    PaymentReconciliation = apps.get_model('payments', 'PaymentReconciliation')

    amount = Decimal(str(amount or '0')).quantize(Decimal('0.01'))
    if amount <= Decimal('0.00'):
        raise ValueError('Refund amount must be greater than zero.')

    reference = (refund_reference or f'REFUND-{payment_session.reference}').strip()
    existing_ledger = PaymentRefundLedger.objects.filter(refund_reference=reference).first()
    existing_refund_total = refund_total_for_payment(payment_session, include_requested=True)
    if existing_ledger:
        existing_refund_total -= Decimal(str(existing_ledger.amount or '0')).quantize(Decimal('0.01'))
    payment_amount = Decimal(str(payment_session.amount or '0')).quantize(Decimal('0.01'))
    if existing_refund_total + amount > payment_amount:
        raise ValueError('Refund amount exceeds the remaining refundable payment amount.')
    refund_scope = _refund_scope(payment_amount=payment_amount, cumulative_refund_amount=existing_refund_total + amount)
    completion_state = _refund_completion_state(refund_scope=refund_scope, status=status)

    try:
        reconciliation = payment_session.reconciliation
    except Exception:
        reconciliation = sync_payment_reconciliation(payment_session)

    ledger, created = PaymentRefundLedger.objects.get_or_create(
        refund_reference=reference,
        defaults={
            'payment_session': payment_session,
            'reconciliation': reconciliation,
            'order': payment_session.order,
            'line': line,
            'refund_type': refund_type or PaymentRefundLedger.TYPE_REFUND,
            'status': status or PaymentRefundLedger.STATUS_REQUESTED,
            'refund_scope': refund_scope,
            'completion_state': completion_state,
            'provider_reference': provider_reference or '',
            'gateway': gateway or payment_session.method,
            'amount': amount,
            'currency': payment_session.currency,
            'reason': reason or '',
            'gateway_payload': gateway_payload or {},
            'requested_by': requested_by if getattr(requested_by, 'is_authenticated', False) else None,
            'reviewed_by': reviewed_by if getattr(reviewed_by, 'is_authenticated', False) else None,
            'processed_at': timezone.now() if status == PaymentRefundLedger.STATUS_SUCCEEDED else None,
            'notes': notes or '',
        },
    )
    if not created:
        if status and ledger.status != status:
            ledger.status = status
            ledger.refund_scope = refund_scope
            ledger.completion_state = completion_state
            if status == PaymentRefundLedger.STATUS_SUCCEEDED and ledger.processed_at is None:
                ledger.processed_at = timezone.now()
            if reviewed_by and getattr(reviewed_by, 'is_authenticated', False):
                ledger.reviewed_by = reviewed_by
            ledger.save(update_fields=['status', 'refund_scope', 'completion_state', 'processed_at', 'reviewed_by', 'updated_at'])
            if status == PaymentRefundLedger.STATUS_SUCCEEDED:
                _post_refund_accounting(ledger)
        return ledger

    total_refunded = refund_total_for_payment(payment_session)
    if total_refunded >= Decimal(str(payment_session.amount or 0)).quantize(Decimal('0.01')):
        reconciliation.status = PaymentReconciliation.STATUS_REFUNDED
        reconciliation.issues = list(dict.fromkeys([*(reconciliation.issues or []), 'Payment has been fully refunded.']))
    else:
        reconciliation.status = PaymentReconciliation.STATUS_MANUAL_REVIEW
        reconciliation.issues = list(dict.fromkeys([*(reconciliation.issues or []), 'Payment has a partial refund.']))
    reconciliation.save(update_fields=['status', 'issues', 'updated_at'])
    if ledger.status == PaymentRefundLedger.STATUS_SUCCEEDED:
        _post_refund_accounting(ledger)
    return ledger


@transaction.atomic
def update_payment_refund_ledger_status(
    refund_ledger,
    *,
    action: str,
    provider_reference: str = '',
    gateway_payload: dict | None = None,
    notes: str = '',
    reviewed_by=None,
):
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    action = (action or '').strip().lower()
    status_by_action = {
        'submit': PaymentRefundLedger.STATUS_SUBMITTED,
        'succeed': PaymentRefundLedger.STATUS_SUCCEEDED,
        'complete': PaymentRefundLedger.STATUS_SUCCEEDED,
        'fail': PaymentRefundLedger.STATUS_FAILED,
        'cancel': PaymentRefundLedger.STATUS_CANCELLED,
    }
    if action not in status_by_action:
        raise ValueError('Unsupported refund action.')
    if refund_ledger.status in {PaymentRefundLedger.STATUS_SUCCEEDED, PaymentRefundLedger.STATUS_FAILED, PaymentRefundLedger.STATUS_CANCELLED}:
        raise ValueError('This refund is already in a terminal state.')

    next_status = status_by_action[action]
    if refund_ledger.status == PaymentRefundLedger.STATUS_REQUESTED and next_status == PaymentRefundLedger.STATUS_SUCCEEDED:
        raise ValueError('Submit the refund before marking it complete.')
    if refund_ledger.status == PaymentRefundLedger.STATUS_SUBMITTED and next_status == PaymentRefundLedger.STATUS_CANCELLED:
        raise ValueError('Submitted refunds should be marked succeeded or failed, not cancelled.')

    refund_ledger.status = next_status
    refund_ledger.completion_state = _refund_completion_state(
        refund_scope=refund_ledger.refund_scope,
        status=next_status,
    )
    if provider_reference:
        refund_ledger.provider_reference = provider_reference.strip()
    if gateway_payload:
        refund_ledger.gateway_payload = {**(refund_ledger.gateway_payload or {}), **gateway_payload}
    if notes:
        refund_ledger.notes = f'{refund_ledger.notes}\n{notes}'.strip()
    if reviewed_by and getattr(reviewed_by, 'is_authenticated', False):
        refund_ledger.reviewed_by = reviewed_by
    if next_status in {PaymentRefundLedger.STATUS_SUCCEEDED, PaymentRefundLedger.STATUS_FAILED, PaymentRefundLedger.STATUS_CANCELLED}:
        refund_ledger.processed_at = timezone.now()
    refund_ledger.save(update_fields=[
        'status',
        'completion_state',
        'provider_reference',
        'gateway_payload',
        'notes',
        'reviewed_by',
        'processed_at',
        'updated_at',
    ])

    _refresh_refund_reconciliation(refund_ledger.payment_session)
    if next_status == PaymentRefundLedger.STATUS_SUCCEEDED:
        from apps.marketplace.payables import create_supplier_debit_adjustments_for_refund, mark_supplier_adjustments_applied_for_source

        create_supplier_debit_adjustments_for_refund(refund_ledger, created_by=reviewed_by)
        mark_supplier_adjustments_applied_for_source(refund_ledger.refund_reference, user=reviewed_by)
        _post_refund_accounting(refund_ledger)
    return refund_ledger


def _refresh_refund_reconciliation(payment_session):
    PaymentReconciliation = apps.get_model('payments', 'PaymentReconciliation')
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    try:
        reconciliation = payment_session.reconciliation
    except Exception:
        reconciliation = sync_payment_reconciliation(payment_session)

    total_refunded = refund_total_for_payment(payment_session)
    payment_amount = Decimal(str(payment_session.amount or '0')).quantize(Decimal('0.01'))
    issues = [
        issue
        for issue in (reconciliation.issues or [])
        if issue not in {'Payment has been fully refunded.', 'Payment has a partial refund.'}
    ]
    if total_refunded >= payment_amount and payment_amount > Decimal('0.00'):
        reconciliation.status = PaymentReconciliation.STATUS_REFUNDED
        issues.append('Payment has been fully refunded.')
        _mark_order_fully_refunded(payment_session.order if payment_session.order_id else None)
    elif PaymentRefundLedger.objects.filter(
        payment_session=payment_session,
        status__in={
            PaymentRefundLedger.STATUS_REQUESTED,
            PaymentRefundLedger.STATUS_SUBMITTED,
            PaymentRefundLedger.STATUS_SUCCEEDED,
        },
    ).exists():
        reconciliation.status = PaymentReconciliation.STATUS_MANUAL_REVIEW
        issues.append('Payment has a partial refund.')
    else:
        reconciliation = sync_payment_reconciliation(payment_session)
        return reconciliation
    reconciliation.issues = list(dict.fromkeys(issues))
    reconciliation.save(update_fields=['status', 'issues', 'updated_at'])
    return reconciliation


def _mark_order_fully_refunded(order) -> None:
    if not order:
        return
    previous_status = order.status or ''
    if previous_status.strip().lower() in {'refunded', 'cancelled', 'canceled'}:
        return
    OrderStatusChange = apps.get_model('order', 'OrderStatusChange')
    OrderStatusChange.objects.create(order=order, old_status=previous_status, new_status='Refunded')
    order.status = 'Refunded'
    order.save(update_fields=['status'])


def _post_payment_accounting(payment_session) -> None:
    try:
        from apps.accounting.services import post_payment_received

        post_payment_received(payment_session)
    except Exception:
        logger.exception('Failed to post payment accounting for %s', getattr(payment_session, 'reference', ''))


def _post_refund_accounting(refund_ledger) -> None:
    try:
        from apps.accounting.services import post_refund

        post_refund(refund_ledger, user=getattr(refund_ledger, 'reviewed_by', None) or getattr(refund_ledger, 'requested_by', None))
    except Exception:
        logger.exception('Failed to post refund accounting for %s', getattr(refund_ledger, 'refund_reference', ''))


def _refund_scope(*, payment_amount: Decimal, cumulative_refund_amount: Decimal) -> str:
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    if payment_amount > Decimal('0.00') and cumulative_refund_amount >= payment_amount:
        return PaymentRefundLedger.SCOPE_FULL
    return PaymentRefundLedger.SCOPE_PARTIAL


def _refund_completion_state(*, refund_scope: str, status: str) -> str:
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    if status == PaymentRefundLedger.STATUS_SUCCEEDED:
        return (
            PaymentRefundLedger.COMPLETION_FULL_COMPLETED
            if refund_scope == PaymentRefundLedger.SCOPE_FULL
            else PaymentRefundLedger.COMPLETION_PARTIAL_COMPLETED
        )
    if status == PaymentRefundLedger.STATUS_SUBMITTED:
        return (
            PaymentRefundLedger.COMPLETION_FULL_SUBMITTED
            if refund_scope == PaymentRefundLedger.SCOPE_FULL
            else PaymentRefundLedger.COMPLETION_PARTIAL_SUBMITTED
        )
    if status == PaymentRefundLedger.STATUS_FAILED:
        return PaymentRefundLedger.COMPLETION_FAILED
    if status == PaymentRefundLedger.STATUS_CANCELLED:
        return PaymentRefundLedger.COMPLETION_CANCELLED
    return (
        PaymentRefundLedger.COMPLETION_FULL_REQUESTED
        if refund_scope == PaymentRefundLedger.SCOPE_FULL
        else PaymentRefundLedger.COMPLETION_PARTIAL_REQUESTED
    )


def refund_total_for_payment(payment_session, *, include_requested: bool = False) -> Decimal:
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    terminal_statuses = {
        PaymentRefundLedger.STATUS_SUBMITTED,
        PaymentRefundLedger.STATUS_SUCCEEDED,
    }
    if include_requested:
        terminal_statuses.add(PaymentRefundLedger.STATUS_REQUESTED)
    total = (
        PaymentRefundLedger.objects.filter(payment_session=payment_session, status__in=terminal_statuses)
        .aggregate(total=Sum('amount'))
    )
    return Decimal(str(total.get('total') or '0')).quantize(Decimal('0.01'))


@transaction.atomic
def create_payment_return_case(
    *,
    payment_session,
    line,
    quantity,
    refund_amount=None,
    reason: str = '',
    restock_decision: str = 'pending',
    condition_note: str = '',
    notes: str = '',
    requested_by=None,
):
    PaymentReturnCase = apps.get_model('payments', 'PaymentReturnCase')

    if payment_session.status not in SUCCESS_PAYMENT_STATUSES:
        raise ValueError('Only paid or authorized payments can have return cases.')
    if not payment_session.order_id:
        raise ValueError('Payment is not linked to an order.')
    if line.order_id != payment_session.order_id:
        raise ValueError('Return line does not belong to the payment order.')

    quantity = int(quantity or 0)
    if quantity <= 0:
        raise ValueError('Return quantity must be greater than zero.')
    if quantity > int(line.quantity or 0):
        raise ValueError('Return quantity cannot exceed the order line quantity.')

    already_in_return_flow = _active_return_quantity_for_line(PaymentReturnCase, line)
    if already_in_return_flow + quantity > int(line.quantity or 0):
        raise ValueError('This order line already has return/refund quantity in progress or completed.')

    amount = _money(refund_amount) if refund_amount is not None else _line_refund_amount(line, quantity)
    if amount <= Decimal('0.00'):
        raise ValueError('Return refund amount must be greater than zero.')
    payment_amount = _money(payment_session.amount)
    if refund_total_for_payment(payment_session, include_requested=True) + amount > payment_amount:
        raise ValueError('Return refund amount exceeds the remaining refundable payment amount.')

    reference = _next_return_reference(PaymentReturnCase)
    reconciliation = _optional_reconciliation(payment_session)
    return PaymentReturnCase.objects.create(
        return_reference=reference,
        payment_session=payment_session,
        reconciliation=reconciliation,
        order=payment_session.order,
        line=line,
        product=getattr(line, 'product', None),
        stockrecord=getattr(line, 'stockrecord', None),
        quantity=quantity,
        accepted_quantity=0,
        refund_amount=amount,
        currency=payment_session.currency or getattr(payment_session.order, 'currency', '') or 'KES',
        restock_decision=restock_decision or PaymentReturnCase.RESTOCK_PENDING,
        condition_note=(condition_note or '').strip(),
        reason=(reason or '').strip(),
        notes=(notes or '').strip(),
        metadata={
            'line_title': getattr(line, 'title', ''),
            'line_quantity': int(line.quantity or 0),
            'unit_refund_amount': str(_line_unit_amount(line)),
        },
        requested_by=requested_by if getattr(requested_by, 'is_authenticated', False) else None,
    )


@transaction.atomic
def update_payment_return_case(
    return_case,
    *,
    action: str,
    accepted_quantity=None,
    restock_decision: str = '',
    condition_note: str = '',
    notes: str = '',
    reviewed_by=None,
):
    PaymentReturnCase = apps.get_model('payments', 'PaymentReturnCase')
    action = (action or '').strip().lower()
    if action not in {'approve', 'receive', 'accept', 'reject', 'refund', 'cancel'}:
        raise ValueError('Unsupported return action.')
    if return_case.status in {PaymentReturnCase.STATUS_REFUNDED, PaymentReturnCase.STATUS_REJECTED, PaymentReturnCase.STATUS_CANCELLED}:
        raise ValueError('This return case is already in a terminal state.')
    allowed_actions = _allowed_return_actions(return_case)
    if action not in allowed_actions:
        allowed = ', '.join(sorted(allowed_actions)) or 'none'
        raise ValueError(f'Return action {action} is not allowed from {return_case.status}. Allowed actions: {allowed}.')

    if condition_note:
        return_case.condition_note = condition_note.strip()
    if notes:
        return_case.notes = f'{return_case.notes}\n{notes}'.strip()
    return_case.reviewed_by = reviewed_by if getattr(reviewed_by, 'is_authenticated', False) else return_case.reviewed_by

    if action == 'approve':
        return_case.status = PaymentReturnCase.STATUS_APPROVED
        metadata = return_case.metadata or {}
        return_case.metadata = {
            **metadata,
            'return_authorization_reference': metadata.get('return_authorization_reference') or f'RMA-{return_case.return_reference}',
            'approved_at': timezone.now().isoformat(),
        }
    elif action == 'receive':
        return_case.status = PaymentReturnCase.STATUS_RECEIVED
        return_case.received_at = timezone.now()
        metadata = return_case.metadata or {}
        return_case.metadata = {
            **metadata,
            'return_receipt_reference': metadata.get('return_receipt_reference') or f'RRCPT-{return_case.return_reference}',
        }
    elif action == 'reject':
        return_case.status = PaymentReturnCase.STATUS_REJECTED
        return_case.restock_decision = PaymentReturnCase.RESTOCK_REJECTED
        return_case.completed_at = timezone.now()
    elif action == 'cancel':
        return_case.status = PaymentReturnCase.STATUS_CANCELLED
        return_case.completed_at = timezone.now()
    elif action in {'accept', 'refund'}:
        quantity = int(accepted_quantity if accepted_quantity is not None else return_case.quantity)
        if quantity <= 0 or quantity > int(return_case.quantity or 0):
            raise ValueError('Accepted quantity must be between 1 and the requested return quantity.')
        already_returned = _accepted_return_quantity_for_line(PaymentReturnCase, return_case.line, exclude_id=return_case.id)
        if already_returned + quantity > int(return_case.line.quantity or 0):
            raise ValueError('Accepted return quantity would exceed the order line quantity.')
        return_case.accepted_quantity = quantity
        return_case.restock_decision = (restock_decision or return_case.restock_decision or PaymentReturnCase.RESTOCK_PENDING).strip()
        if action == 'accept':
            return_case.status = PaymentReturnCase.STATUS_ACCEPTED
        else:
            return_case.status = PaymentReturnCase.STATUS_REFUNDED
            return_case.completed_at = timezone.now()
        _apply_return_restock(return_case)
        refund_ledger = None
        if action == 'refund':
            refund_ledger = _ensure_return_refund_ledger(return_case, reviewed_by=reviewed_by)
            return_case.refund_ledger = refund_ledger
        metadata = return_case.metadata or {}
        adjustments = []
        if action == 'refund' and metadata.get('supplier_return_applied_at'):
            from apps.marketplace.payables import mark_supplier_adjustments_applied_for_source

            adjustments = mark_supplier_adjustments_applied_for_source(return_case.return_reference, user=reviewed_by)
        elif not metadata.get('supplier_return_applied_at'):
            from apps.marketplace.payables import apply_supplier_return_to_payables

            adjustments = apply_supplier_return_to_payables(return_case, created_by=reviewed_by)
            metadata = {
                **metadata,
                'supplier_return_applied_at': timezone.now().isoformat(),
            }
        return_case.metadata = {
            **metadata,
            'supplier_adjustment_count': len(adjustments) if adjustments else metadata.get('supplier_adjustment_count', 0),
            **(
                {
                    'refund_ledger_id': refund_ledger.id,
                    'refund_reference': refund_ledger.refund_reference,
                }
                if refund_ledger
                else {}
            ),
            'credit_note_reference': metadata.get('credit_note_reference') or f'CN-{return_case.return_reference}',
            'refund_payment_reference': (
                metadata.get('refund_payment_reference')
                or (f'PE-{return_case.return_reference}' if action == 'refund' else '')
            ),
        }
        if refund_ledger:
            _queue_return_credit_note_export(refund_ledger)

    return_case.save()
    return return_case


def _allowed_return_actions(return_case) -> set[str]:
    PaymentReturnCase = apps.get_model('payments', 'PaymentReturnCase')
    transitions = {
        PaymentReturnCase.STATUS_REQUESTED: {'approve', 'reject', 'cancel'},
        PaymentReturnCase.STATUS_APPROVED: {'receive', 'reject', 'cancel'},
        PaymentReturnCase.STATUS_RECEIVED: {'accept', 'reject', 'cancel'},
        PaymentReturnCase.STATUS_ACCEPTED: {'refund'},
    }
    return transitions.get(return_case.status, set())


def _ensure_return_refund_ledger(return_case, *, reviewed_by=None):
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
    status = (
        PaymentRefundLedger.STATUS_SUCCEEDED
        if return_case.status == apps.get_model('payments', 'PaymentReturnCase').STATUS_REFUNDED
        else PaymentRefundLedger.STATUS_REQUESTED
    )
    reference = f'RETURN-{return_case.return_reference}'
    ledger = record_payment_refund_ledger(
        return_case.payment_session,
        amount=return_case.refund_amount,
        reason=return_case.reason or 'Customer return accepted.',
        refund_reference=reference,
        refund_type=PaymentRefundLedger.TYPE_RETURN,
        status=status,
        gateway='return',
        requested_by=return_case.requested_by,
        reviewed_by=reviewed_by,
        line=return_case.line,
        notes=f'Return case {return_case.return_reference}; ERPNext rule: credit_note.',
    )
    return ledger


def _apply_return_restock(return_case):
    PaymentReturnCase = apps.get_model('payments', 'PaymentReturnCase')
    if return_case.restock_decision != PaymentReturnCase.RESTOCK_RESTOCK:
        return
    if return_case.restocked_at or not return_case.stockrecord_id:
        return
    stockrecord = return_case.stockrecord
    stockrecord.num_in_stock = int(stockrecord.num_in_stock or 0) + int(return_case.accepted_quantity or 0)
    stockrecord.save(update_fields=['num_in_stock'])
    return_case.restocked_at = timezone.now()


def _queue_return_credit_note_export(refund_ledger) -> None:
    _queue_refund_credit_note_export(refund_ledger)


def _queue_refund_credit_note_export(refund_ledger) -> None:
    from apps.common.async_utils import dispatch_background_task
    from apps.integrations.tasks import export_refund_credit_note_to_erpnext

    dispatch_background_task(
        export_refund_credit_note_to_erpnext,
        run_kwargs={
            'payment_reference': refund_ledger.payment_session.reference,
            'refund_amount': str(refund_ledger.amount),
            'reason': refund_ledger.reason,
            'refund_reference': refund_ledger.refund_reference,
        },
        async_kwargs={
            'payment_reference': refund_ledger.payment_session.reference,
            'refund_amount': str(refund_ledger.amount),
            'reason': refund_ledger.reason,
            'refund_reference': refund_ledger.refund_reference,
        },
    )


def _accepted_return_quantity_for_line(PaymentReturnCase, line, *, exclude_id=None) -> int:
    active_statuses = {
        PaymentReturnCase.STATUS_ACCEPTED,
        PaymentReturnCase.STATUS_REFUNDED,
    }
    return _return_quantity_for_line(PaymentReturnCase, line, active_statuses, quantity_field='accepted_quantity', exclude_id=exclude_id)


def _active_return_quantity_for_line(PaymentReturnCase, line, *, exclude_id=None) -> int:
    open_statuses = {
        PaymentReturnCase.STATUS_REQUESTED,
        PaymentReturnCase.STATUS_APPROVED,
        PaymentReturnCase.STATUS_RECEIVED,
    }
    completed_statuses = {
        PaymentReturnCase.STATUS_ACCEPTED,
        PaymentReturnCase.STATUS_REFUNDED,
    }
    return (
        _return_quantity_for_line(PaymentReturnCase, line, open_statuses, quantity_field='quantity', exclude_id=exclude_id)
        + _return_quantity_for_line(
            PaymentReturnCase,
            line,
            completed_statuses,
            quantity_field='accepted_quantity',
            exclude_id=exclude_id,
        )
    )


def _return_quantity_for_line(PaymentReturnCase, line, statuses, *, quantity_field='quantity', exclude_id=None) -> int:
    queryset = PaymentReturnCase.objects.filter(line=line, status__in=statuses)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    total = queryset.aggregate(total=Sum(quantity_field))
    return int(total.get('total') or 0)


def _optional_reconciliation(payment_session):
    try:
        return payment_session.reconciliation
    except Exception:
        return sync_payment_reconciliation(payment_session)


def _line_unit_amount(line) -> Decimal:
    quantity = Decimal(str(line.quantity or 0))
    if quantity <= Decimal('0'):
        return Decimal('0.00')
    return (Decimal(str(line.line_price_incl_tax or 0)) / quantity).quantize(Decimal('0.01'))


def _line_refund_amount(line, quantity: int) -> Decimal:
    return (_line_unit_amount(line) * Decimal(str(quantity or 0))).quantize(Decimal('0.01'))


def _next_return_reference(PaymentReturnCase):
    prefix = f'RTN-{timezone.now():%Y%m%d}'
    count = PaymentReturnCase.objects.filter(return_reference__startswith=prefix).count() + 1
    return f'{prefix}-{count:04d}'


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
    safe_message = str(message or '')
    if len(safe_message) > 255:
        safe_message = f'{safe_message[:252]}...'
    return PaymentEvent.objects.create(
        payment_session=payment_session,
        kind=kind,
        status_before=status_before or '',
        status_after=status_after or '',
        external_reference=external_reference or '',
        message=safe_message,
        payload=payload or {},
    )


def _queue_paid_order_accounting_export(payment_session) -> None:
    from apps.common.async_utils import dispatch_background_task
    from apps.integrations.tasks import export_paid_order_accounting_to_erpnext

    dispatch_background_task(
        export_paid_order_accounting_to_erpnext,
        run_kwargs={'payment_reference': payment_session.reference},
        async_kwargs={'payment_reference': payment_session.reference},
    )


def _notify_admin_payment_status(payment_session, *, previous_status: str = '') -> None:
    from apps.notifications.services import create_admin_notification

    method = payment_method_definition(payment_session.method) or {}
    method_name = method.get('name') or payment_session.method
    amount = f'{payment_session.currency} {payment_session.amount}'
    if payment_session.status in SUCCESS_PAYMENT_STATUSES:
        create_admin_notification(
            event_type='payment_confirmed',
            event_key=f'payment-confirmed:{payment_session.reference}',
            title='Payment confirmed',
            message=f'{method_name} payment {payment_session.reference} for {amount} was confirmed.',
            severity='success',
            action_url=f'/payment-logs?reference={payment_session.reference}',
            related_object_type='payment_session',
            related_object_id=payment_session.reference,
            metadata={
                'reference': payment_session.reference,
                'previous_status': previous_status,
                'status': payment_session.status,
                'method': payment_session.method,
                'amount': str(payment_session.amount),
                'currency': payment_session.currency,
            },
        )
    elif payment_session.status == payment_session.STATUS_FAILED:
        create_admin_notification(
            event_type='payment_failed',
            event_key=f'payment-failed:{payment_session.reference}',
            title='Payment failed',
            message=f'{method_name} payment {payment_session.reference} for {amount} failed.',
            severity='error',
            action_url=f'/payment-logs?reference={payment_session.reference}',
            related_object_type='payment_session',
            related_object_id=payment_session.reference,
            metadata={
                'reference': payment_session.reference,
                'previous_status': previous_status,
                'status': payment_session.status,
                'method': payment_session.method,
                'amount': str(payment_session.amount),
                'currency': payment_session.currency,
            },
        )


def _notify_admin_paid_order(payment_session) -> None:
    from apps.notifications.services import create_admin_notification

    order = payment_session.order
    if not order:
        return
    create_admin_notification(
        event_type='paid_order_created',
        event_key=f'paid-order:{order.number}',
        title='Paid order ready',
        message=f'Order {order.number} has a confirmed {payment_session.method} payment.',
        severity='success',
        action_url=f'/orders/{order.id}',
        related_object_type='order',
        related_object_id=str(order.number),
        metadata={
            'order_id': order.id,
            'order_number': order.number,
            'payment_reference': payment_session.reference,
            'method': payment_session.method,
            'amount': str(payment_session.amount),
            'currency': payment_session.currency,
        },
    )


def serialize_payment_session(payment_session) -> dict:
    method = payment_method_definition(payment_session.method) or {}
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
