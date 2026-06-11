import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from .config import get_payment_setting, provider_is_enabled
from .services import confirm_payment_session, log_payment_event


class PesapalConfigurationError(Exception):
    pass


class PesapalGatewayError(Exception):
    pass


SUCCESS_STATUS_CODES = {'1'}
FAILED_STATUS_CODES = {'0', '2', '3'}


def pesapal_is_configured() -> bool:
    if not provider_is_enabled('pesapal', default=True):
        return False
    required = [
        get_payment_setting('pesapal', 'consumer_key', ''),
        get_payment_setting('pesapal', 'consumer_secret', ''),
        get_payment_setting('pesapal', 'base_url', ''),
        get_payment_setting('pesapal', 'callback_url', ''),
        get_payment_setting('pesapal', 'ipn_id', ''),
    ]
    return all(required)


def submit_order_request(payment_session, *, customer_name: str = '') -> dict:
    if not pesapal_is_configured():
        raise PesapalConfigurationError('Pesapal credentials and callback settings are not configured.')

    token = _request_access_token()
    payload = {
        'id': payment_session.reference,
        'currency': payment_session.currency,
        'amount': float(Decimal(str(payment_session.amount)).quantize(Decimal('0.01'))),
        'description': f'Vortexus payment {payment_session.reference}'[:100],
        'redirect_mode': get_payment_setting('pesapal', 'redirect_mode', settings.PESAPAL_REDIRECT_MODE),
        'callback_url': get_payment_setting('pesapal', 'callback_url', ''),
        'notification_id': get_payment_setting('pesapal', 'ipn_id', ''),
        'billing_address': {
            'email_address': payment_session.payer_email,
            'phone_number': payment_session.payer_phone,
            'first_name': _first_name(customer_name),
            'last_name': _last_name(customer_name),
        },
    }
    cancellation_url = get_payment_setting('pesapal', 'cancellation_url', '')
    if cancellation_url:
        payload['cancellation_url'] = cancellation_url
    branch = get_payment_setting('pesapal', 'branch', '')
    if branch:
        payload['branch'] = branch

    previous_status = payment_session.status
    response_data = _post_json('/Transactions/SubmitOrderRequest', payload, token=token)
    order_tracking_id = response_data.get('order_tracking_id') or ''
    redirect_url = response_data.get('redirect_url') or ''
    if not order_tracking_id or not redirect_url:
        raise PesapalGatewayError('Pesapal did not return an order tracking ID and redirect URL.')

    payment_session.status = payment_session.STATUS_PENDING
    payment_session.external_reference = order_tracking_id
    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'order_tracking_id': order_tracking_id,
        'merchant_reference': response_data.get('merchant_reference', payment_session.reference),
        'redirect_url': redirect_url,
        'redirect_mode': get_payment_setting('pesapal', 'redirect_mode', settings.PESAPAL_REDIRECT_MODE),
        'pesapal_response': response_data,
    }
    payment_session.metadata = {
        **payment_session.metadata,
        'integration': 'pesapal_api_3',
    }
    payment_session.save(update_fields=['status', 'external_reference', 'provider_payload', 'metadata', 'updated_at'])
    log_payment_event(
        payment_session,
        kind='provider_submitted',
        status_before=previous_status,
        status_after=payment_session.status,
        external_reference=order_tracking_id,
        payload={'pesapal_response': response_data},
    )
    return payment_session.provider_payload


def query_transaction_status(payment_session) -> dict:
    order_tracking_id = payment_session.external_reference or payment_session.provider_payload.get('order_tracking_id', '')
    if not order_tracking_id:
        raise PesapalGatewayError('Missing Pesapal order tracking ID for this payment session.')
    token = _request_access_token()
    return _get_json(f'/Transactions/GetTransactionStatus?{urlencode({"orderTrackingId": order_tracking_id})}', token=token)


def handle_transaction_status(payment_session, status_payload: dict):
    _validate_status_payload(payment_session, status_payload)

    previous_status = payment_session.status

    payment_status_code = str(status_payload.get('status_code') or status_payload.get('payment_status_code') or '').strip()
    payment_status = str(status_payload.get('payment_status_description') or status_payload.get('payment_status') or '').strip()
    confirmation_code = str(status_payload.get('confirmation_code') or '').strip()
    payment_method = str(status_payload.get('payment_method') or '').strip()
    payment_account = str(status_payload.get('payment_account') or '').strip()

    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'last_status': status_payload,
    }
    payment_session.save(update_fields=['provider_payload', 'updated_at'])
    log_payment_event(
        payment_session,
        kind='status_queried',
        status_before=previous_status,
        status_after=payment_session.status,
        external_reference=payment_session.external_reference,
        payload={'status_payload': status_payload},
    )

    metadata = {
        'pesapal_status_code': payment_status_code,
        'pesapal_status': payment_status,
        'pesapal_payment_method': payment_method,
        'pesapal_payment_account': payment_account,
        'confirmed_via': 'pesapal_status_query',
    }
    if confirmation_code:
        metadata['pesapal_confirmation_code'] = confirmation_code

    if payment_status_code in SUCCESS_STATUS_CODES:
        return confirm_payment_session(
            payment_session,
            success=True,
            external_reference=payment_session.external_reference or confirmation_code,
            metadata=metadata,
        )
    if payment_status_code in FAILED_STATUS_CODES:
        return confirm_payment_session(
            payment_session,
            success=False,
            external_reference=payment_session.external_reference or confirmation_code,
            metadata=metadata,
        )
    return payment_session


def find_payment_by_order_tracking_id(PaymentSession, order_tracking_id: str):
    order_tracking_id = (order_tracking_id or '').strip()
    if not order_tracking_id:
        return None
    payment = PaymentSession.objects.filter(external_reference=order_tracking_id, method='pesapal').first()
    if payment:
        return payment
    return PaymentSession.objects.filter(provider_payload__order_tracking_id=order_tracking_id, method='pesapal').first()


def _request_access_token() -> str:
    payload = {
        'consumer_key': get_payment_setting('pesapal', 'consumer_key', ''),
        'consumer_secret': get_payment_setting('pesapal', 'consumer_secret', ''),
    }
    response_data = _post_json('/Auth/RequestToken', payload)
    token = response_data.get('token', '')
    if not token:
        raise PesapalGatewayError('Pesapal did not return an access token.')
    return token


def _post_json(path: str, payload: dict, *, token: str = '') -> dict:
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = Request(url=_url(path), data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    return _execute_request(request)


def _get_json(path: str, *, token: str) -> dict:
    request = Request(url=_url(path), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}, method='GET')
    return _execute_request(request)


def _execute_request(request: Request) -> dict:
    try:
        with urlopen(request, timeout=int(get_payment_setting('pesapal', 'timeout_seconds', settings.PESAPAL_TIMEOUT_SECONDS))) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:  # pragma: no cover
        body = exc.read().decode('utf-8', errors='ignore')
        raise PesapalGatewayError(f'Pesapal gateway returned HTTP {exc.code}: {body or exc.reason}') from exc
    except URLError as exc:  # pragma: no cover
        raise PesapalGatewayError(f'Unable to reach Pesapal gateway: {exc.reason}') from exc


def _url(path: str) -> str:
    base_url = str(get_payment_setting('pesapal', 'base_url', settings.PESAPAL_BASE_URL)).rstrip('/')
    return f'{base_url}{path}'


def _validate_status_payload(payment_session, status_payload: dict) -> None:
    merchant_reference = str(status_payload.get('merchant_reference') or '').strip()
    if merchant_reference and merchant_reference != payment_session.reference:
        raise PesapalGatewayError('Pesapal merchant reference did not match this payment session.')

    currency = str(status_payload.get('currency') or '').strip()
    if currency and currency.upper() != str(payment_session.currency).upper():
        raise PesapalGatewayError('Pesapal currency did not match this payment session.')

    amount = status_payload.get('amount')
    if amount not in (None, ''):
        try:
            received_amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        except Exception as exc:
            raise PesapalGatewayError('Pesapal returned an invalid transaction amount.') from exc
        expected_amount = Decimal(str(payment_session.amount)).quantize(Decimal('0.01'))
        if received_amount != expected_amount:
            raise PesapalGatewayError('Pesapal amount did not match this payment session.')


def _first_name(name: str) -> str:
    parts = [part for part in str(name or '').strip().split() if part]
    return parts[0] if parts else ''


def _last_name(name: str) -> str:
    parts = [part for part in str(name or '').strip().split() if part]
    return ' '.join(parts[1:]) if len(parts) > 1 else ''
