import base64
import json
from datetime import datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import settings

from .config import get_payment_setting, provider_is_enabled
from .services import confirm_payment_session


class MpesaConfigurationError(Exception):
    pass


class MpesaGatewayError(Exception):
    pass


def mpesa_is_configured() -> bool:
    if not provider_is_enabled('mpesa', default=True):
        return False
    required = [
        get_payment_setting('mpesa', 'consumer_key', ''),
        get_payment_setting('mpesa', 'consumer_secret', ''),
        get_payment_setting('mpesa', 'shortcode', ''),
        get_payment_setting('mpesa', 'passkey', ''),
        get_payment_setting('mpesa', 'callback_url', ''),
    ]
    return all(required)


def initiate_stk_push(payment_session) -> dict:
    if not mpesa_is_configured():
        raise MpesaConfigurationError('M-Pesa Daraja credentials are not configured.')

    access_token = _generate_access_token()
    timestamp = _timestamp()
    password = _password(timestamp)
    phone_number = _normalize_phone_number(payment_session.payer_phone)

    payload = {
        'BusinessShortCode': get_payment_setting('mpesa', 'shortcode', ''),
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': get_payment_setting('mpesa', 'transaction_type', 'CustomerPayBillOnline'),
        'Amount': int(Decimal(str(payment_session.amount)).quantize(Decimal('1'))),
        'PartyA': phone_number,
        'PartyB': get_payment_setting('mpesa', 'shortcode', ''),
        'PhoneNumber': phone_number,
        'CallBackURL': get_payment_setting('mpesa', 'callback_url', ''),
        'AccountReference': payment_session.reference,
        'TransactionDesc': f'Reesolmart payment {payment_session.reference}',
    }

    response_data = _post_json(
        url=f'{_base_url()}/mpesa/stkpush/v1/processrequest',
        payload=payload,
        headers={'Authorization': f'Bearer {access_token}'},
    )

    provider_payload = payment_session.provider_payload.copy()
    provider_payload.update(
        {
            'merchant_request_id': response_data.get('MerchantRequestID', ''),
            'checkout_request_id': response_data.get('CheckoutRequestID', ''),
            'customer_message': response_data.get('CustomerMessage', ''),
            'response_code': response_data.get('ResponseCode', ''),
            'response_description': response_data.get('ResponseDescription', ''),
        }
    )
    payment_session.provider_payload = provider_payload
    payment_session.status = payment_session.STATUS_PENDING
    payment_session.save(update_fields=['provider_payload', 'status', 'updated_at'])

    return provider_payload


def query_stk_push_status(payment_session) -> dict:
    if not mpesa_is_configured():
        raise MpesaConfigurationError('M-Pesa Daraja credentials are not configured.')

    checkout_request_id = payment_session.provider_payload.get('checkout_request_id', '')
    if not checkout_request_id:
        raise MpesaGatewayError('Missing CheckoutRequestID for this payment session.')

    access_token = _generate_access_token()
    timestamp = _timestamp()
    payload = {
        'BusinessShortCode': get_payment_setting('mpesa', 'shortcode', ''),
        'Password': _password(timestamp),
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    return _post_json(
        url=f'{_base_url()}/mpesa/stkpushquery/v1/query',
        payload=payload,
        headers={'Authorization': f'Bearer {access_token}'},
    )


def handle_stk_query_result(payment_session, query_payload: dict):
    result_code = query_payload.get('ResultCode')
    if result_code is None:
        return payment_session

    result_code = str(result_code)
    result_desc = query_payload.get('ResultDesc', '')
    checkout_request_id = query_payload.get('CheckoutRequestID', '') or payment_session.provider_payload.get('checkout_request_id', '')
    merchant_request_id = query_payload.get('MerchantRequestID', '') or payment_session.provider_payload.get('merchant_request_id', '')
    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'query_result_code': result_code,
        'query_result_desc': result_desc,
    }
    payment_session.save(update_fields=['provider_payload', 'updated_at'])

    if result_code == '0':
        return confirm_payment_session(
            payment_session,
            success=True,
            external_reference=checkout_request_id or merchant_request_id,
            metadata={
                'mpesa_result_code': result_code,
                'mpesa_result_desc': result_desc,
                'confirmed_via': 'stk_query',
            },
        )

    if result_code in {'1', '1032', '1037', '2001'}:
        return confirm_payment_session(
            payment_session,
            success=False,
            external_reference=checkout_request_id or merchant_request_id,
            metadata={
                'mpesa_result_code': result_code,
                'mpesa_result_desc': result_desc,
                'confirmed_via': 'stk_query',
            },
        )

    return payment_session


def handle_callback(payment_session, callback_payload: dict):
    stk_callback = ((callback_payload or {}).get('Body') or {}).get('stkCallback') or {}
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc', '')
    merchant_request_id = stk_callback.get('MerchantRequestID', '')
    checkout_request_id = stk_callback.get('CheckoutRequestID', '')
    callback_metadata = _metadata_items_to_dict(stk_callback.get('CallbackMetadata', {}).get('Item', []))

    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'merchant_request_id': merchant_request_id or payment_session.provider_payload.get('merchant_request_id', ''),
        'checkout_request_id': checkout_request_id or payment_session.provider_payload.get('checkout_request_id', ''),
        'callback_result_code': result_code,
        'callback_result_desc': result_desc,
        'callback_metadata': callback_metadata,
    }
    payment_session.save(update_fields=['provider_payload', 'updated_at'])

    success = str(result_code) == '0'
    return confirm_payment_session(
        payment_session,
        success=success,
        external_reference=checkout_request_id or merchant_request_id,
        metadata={
            'mpesa_result_code': result_code,
            'mpesa_result_desc': result_desc,
            'mpesa_receipt_number': callback_metadata.get('MpesaReceiptNumber', ''),
        },
    )


def find_payment_by_callback_reference(PaymentSession, callback_payload: dict):
    stk_callback = ((callback_payload or {}).get('Body') or {}).get('stkCallback') or {}
    merchant_request_id = stk_callback.get('MerchantRequestID', '')
    checkout_request_id = stk_callback.get('CheckoutRequestID', '')

    if checkout_request_id:
        payment = PaymentSession.objects.filter(provider_payload__checkout_request_id=checkout_request_id).first()
        if payment:
            return payment
    if merchant_request_id:
        payment = PaymentSession.objects.filter(provider_payload__merchant_request_id=merchant_request_id).first()
        if payment:
            return payment
    return None


def _generate_access_token() -> str:
    credentials = f'{get_payment_setting("mpesa", "consumer_key", "")}:{get_payment_setting("mpesa", "consumer_secret", "")}'.encode('utf-8')
    basic_auth = base64.b64encode(credentials).decode('utf-8')
    url = f"{_base_url()}/oauth/v1/generate?{urlencode({'grant_type': 'client_credentials'})}"
    response = _request_json(url, headers={'Authorization': f'Basic {basic_auth}'})
    access_token = response.get('access_token', '')
    if not access_token:
        raise MpesaGatewayError('Unable to obtain M-Pesa access token.')
    return access_token


def _post_json(*, url: str, payload: dict, headers: dict | None = None) -> dict:
    request_headers = {'Content-Type': 'application/json'}
    if headers:
        request_headers.update(headers)
    request = Request(url=url, data=json.dumps(payload).encode('utf-8'), headers=request_headers, method='POST')
    return _execute_request(request)


def _request_json(url: str, headers: dict | None = None) -> dict:
    request = Request(url=url, headers=headers or {}, method='GET')
    return _execute_request(request)


def _execute_request(request: Request) -> dict:
    try:
        with urlopen(request, timeout=int(get_payment_setting('mpesa', 'timeout_seconds', settings.MPESA_TIMEOUT_SECONDS))) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:  # pragma: no cover
        body = exc.read().decode('utf-8', errors='ignore')
        raise MpesaGatewayError(f'M-Pesa gateway returned HTTP {exc.code}: {body}') from exc
    except URLError as exc:  # pragma: no cover
        raise MpesaGatewayError(f'Unable to reach M-Pesa gateway: {exc.reason}') from exc
    except TimeoutError as exc:  # pragma: no cover
        raise MpesaGatewayError('M-Pesa gateway request timed out.') from exc
    except OSError as exc:  # pragma: no cover
        raise MpesaGatewayError(f'Unable to reach M-Pesa gateway: {exc}') from exc


def _base_url() -> str:
    raw_url = str(get_payment_setting('mpesa', 'base_url', settings.MPESA_BASE_URL) or settings.MPESA_BASE_URL).strip()
    parsed = urlsplit(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise MpesaConfigurationError('M-Pesa base URL must be an absolute URL.')
    return urlunsplit((parsed.scheme, parsed.netloc, '', '', '')).rstrip('/')


def _timestamp() -> str:
    return datetime.utcnow().strftime('%Y%m%d%H%M%S')


def _password(timestamp: str) -> str:
    token = f'{get_payment_setting("mpesa", "shortcode", "")}{get_payment_setting("mpesa", "passkey", "")}{timestamp}'.encode('utf-8')
    return base64.b64encode(token).decode('utf-8')


def _normalize_phone_number(phone_number: str) -> str:
    digits = ''.join(ch for ch in str(phone_number or '') if ch.isdigit())
    if digits.startswith('0'):
        digits = f'254{digits[1:]}'
    elif digits.startswith('7'):
        digits = f'254{digits}'
    if not digits.startswith('254'):
        raise MpesaGatewayError('M-Pesa phone number must be a Kenyan MSISDN.')
    return digits


def _metadata_items_to_dict(items: list[dict]) -> dict:
    metadata = {}
    for item in items or []:
        name = item.get('Name')
        if not name:
            continue
        metadata[name] = item.get('Value')
    return metadata
