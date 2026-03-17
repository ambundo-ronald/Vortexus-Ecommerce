from django.conf import settings

from .services import confirm_payment_session


class AirtelMoneyGatewayError(Exception):
    pass


def airtel_money_is_configured() -> bool:
    return settings.AIRTEL_MONEY_SANDBOX_ENABLED


def initiate_airtel_collection(payment_session) -> dict:
    if not airtel_money_is_configured():
        raise AirtelMoneyGatewayError('Airtel Money sandbox is disabled on this backend.')

    phone_number = _normalize_phone_number(payment_session.payer_phone)
    provider_payload = {
        **payment_session.provider_payload,
        'provider': settings.AIRTEL_MONEY_PROVIDER_NAME,
        'channel': 'airtel_collection',
        'provider_reference': f'AIRTEL-{payment_session.reference}',
        'customer_message': 'Approve the Airtel Money prompt on the handset to complete payment.',
        'phone_number': phone_number,
    }
    payment_session.provider_payload = provider_payload
    payment_session.status = payment_session.STATUS_PENDING
    payment_session.save(update_fields=['provider_payload', 'status', 'updated_at'])
    return provider_payload


def handle_airtel_callback(payment_session, callback_payload: dict):
    transaction = callback_payload.get('transaction', {}) if isinstance(callback_payload, dict) else {}
    status_value = (transaction.get('status') or callback_payload.get('status') or '').strip().lower()
    success = status_value in {'success', 'successful', 'paid', 'completed'}
    external_reference = (
        transaction.get('airtel_money_id')
        or transaction.get('reference')
        or callback_payload.get('reference')
        or payment_session.external_reference
    )

    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'callback_payload': callback_payload,
    }
    payment_session.save(update_fields=['provider_payload', 'updated_at'])

    return confirm_payment_session(
        payment_session,
        success=success,
        external_reference=external_reference or payment_session.reference,
        metadata={
            'airtel_status': status_value,
            'airtel_transaction_id': transaction.get('airtel_money_id', ''),
        },
    )


def find_payment_by_airtel_reference(PaymentSession, callback_payload: dict):
    transaction = callback_payload.get('transaction', {}) if isinstance(callback_payload, dict) else {}
    reference = transaction.get('reference') or callback_payload.get('reference') or ''
    provider_reference = transaction.get('provider_reference') or callback_payload.get('provider_reference') or ''

    if reference:
        payment = PaymentSession.objects.filter(reference=reference, method='airtel_money').first()
        if payment:
            return payment
    if provider_reference:
        payment = PaymentSession.objects.filter(provider_payload__provider_reference=provider_reference, method='airtel_money').first()
        if payment:
            return payment
    return None


def _normalize_phone_number(phone_number: str) -> str:
    digits = ''.join(ch for ch in str(phone_number or '') if ch.isdigit())
    if digits.startswith('0'):
        digits = f'254{digits[1:]}'
    elif digits.startswith('7'):
        digits = f'254{digits}'
    if not digits.startswith('254'):
        raise AirtelMoneyGatewayError('Airtel Money phone number must be a Kenyan MSISDN.')
    return digits
