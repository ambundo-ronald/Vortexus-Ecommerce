from decimal import Decimal
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.utils import timezone


def available_payment_methods() -> list[dict]:
    return [method.copy() for method in settings.PAYMENT_METHODS]


def get_payment_method(code: str) -> dict | None:
    normalized = (code or '').strip()
    for method in settings.PAYMENT_METHODS:
        if method['code'] == normalized:
            return method.copy()
    return None


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
    return session


def confirm_payment_session(payment_session, *, success: bool, external_reference: str = '', metadata: dict | None = None):
    payment_session.external_reference = external_reference or payment_session.external_reference
    merged_metadata = payment_session.metadata.copy()
    if metadata:
        merged_metadata.update(metadata)
    payment_session.metadata = merged_metadata
    if success:
        payment_session.status = _success_status_for_method(payment_session.method)
        payment_session.paid_at = timezone.now()
    else:
        payment_session.status = payment_session.STATUS_FAILED
    payment_session.save(update_fields=['external_reference', 'metadata', 'status', 'paid_at', 'updated_at'])
    return payment_session


def link_payment_to_order(payment_session, order):
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

    return source


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
