import json
from decimal import Decimal, ROUND_CEILING
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
        'description': f'Reesolmart payment {payment_session.reference}'[:100],
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
    _raise_for_pesapal_error(response_data)
    order_tracking_id = response_data.get('order_tracking_id') or ''
    redirect_url = response_data.get('redirect_url') or ''
    if not order_tracking_id or not redirect_url:
        raise PesapalGatewayError(_response_message(response_data) or 'Pesapal did not return an order tracking ID and redirect URL.')

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
    response_data = _get_json(f'/Transactions/GetTransactionStatus?{urlencode({"orderTrackingId": order_tracking_id})}', token=token)
    _raise_for_pesapal_error(response_data)
    return response_data


def register_ipn_url(*, ipn_url: str | None = None, notification_type: str | None = None) -> dict:
    if not get_payment_setting('pesapal', 'consumer_key', '') or not get_payment_setting('pesapal', 'consumer_secret', ''):
        raise PesapalConfigurationError('Pesapal consumer key and secret are required before registering IPN.')

    url = (ipn_url or get_payment_setting('pesapal', 'ipn_url', settings.PESAPAL_IPN_URL) or '').strip()
    if not url:
        raise PesapalConfigurationError('Pesapal IPN URL is required before registering IPN.')

    ipn_notification_type = (
        notification_type
        or get_payment_setting('pesapal', 'notification_type', settings.PESAPAL_IPN_NOTIFICATION_TYPE)
        or 'POST'
    ).strip().upper()
    token = _request_access_token()
    response_data = _post_json(
        '/URLSetup/RegisterIPN',
        {'url': url, 'ipn_notification_type': ipn_notification_type},
        token=token,
    )
    _raise_for_pesapal_error(response_data)
    ipn_id = str(response_data.get('ipn_id') or response_data.get('notification_id') or '').strip()
    if not ipn_id:
        raise PesapalGatewayError(_response_message(response_data) or 'Pesapal did not return an IPN ID.')
    return response_data


def request_refund(payment_session, *, amount, username: str, remarks: str) -> dict:
    confirmation_code = str((payment_session.metadata or {}).get('pesapal_confirmation_code') or '').strip()
    if not confirmation_code:
        raise PesapalGatewayError('Missing Pesapal confirmation code for refund request.')

    token = _request_access_token()
    payload = {
        'confirmation_code': confirmation_code,
        'amount': str(Decimal(str(amount)).quantize(Decimal('0.01'))),
        'username': (username or '').strip() or 'Reesolmart Admin',
        'remarks': (remarks or '').strip() or f'Refund for {payment_session.reference}',
    }
    response_data = _post_json('/Transactions/RefundRequest', payload, token=token)
    _raise_for_pesapal_error(response_data)
    status_code = str(response_data.get('status') or response_data.get('error') or '').strip()
    message = str(response_data.get('message') or '').strip()
    if status_code and status_code != '200':
        raise PesapalGatewayError(message or f'Pesapal refund request rejected with status {status_code}.')
    return response_data


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
    _raise_for_pesapal_error(response_data)
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


def _response_message(response_data: dict) -> str:
    if not isinstance(response_data, dict):
        return ''
    error = response_data.get('error')
    if isinstance(error, dict):
        return str(error.get('message') or error.get('code') or '').strip()
    return str(response_data.get('message') or response_data.get('description') or '').strip()


def _raise_for_pesapal_error(response_data: dict) -> None:
    if not isinstance(response_data, dict):
        return
    error = response_data.get('error')
    if error:
        if isinstance(error, dict):
            if not any(value not in (None, '') for value in error.values()):
                error = None
            else:
                message = str(error.get('message') or error.get('code') or error).strip()
                raise PesapalGatewayError(message or 'Pesapal gateway returned an error.')
        if error:
            message = str(error).strip()
            raise PesapalGatewayError(message or 'Pesapal gateway returned an error.')

    status_code = str(response_data.get('status') or '').strip()
    if status_code and status_code not in {'200', '201'}:
        message = _response_message(response_data)
        raise PesapalGatewayError(message or f'Pesapal gateway returned status {status_code}.')


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
        rounded_expected = expected_amount.to_integral_value(rounding=ROUND_CEILING)
        allows_pesapal_rounding = (
            str(payment_session.currency).upper() == 'KES'
            and received_amount == rounded_expected
            and Decimal('0.00') <= (received_amount - expected_amount) < Decimal('1.00')
        )
        if received_amount != expected_amount and not allows_pesapal_rounding:
            raise PesapalGatewayError('Pesapal amount did not match this payment session.')


def _first_name(name: str) -> str:
    parts = [part for part in str(name or '').strip().split() if part]
    return parts[0] if parts else ''


def _last_name(name: str) -> str:
    parts = [part for part in str(name or '').strip().split() if part]
    return ' '.join(parts[1:]) if len(parts) > 1 else ''
