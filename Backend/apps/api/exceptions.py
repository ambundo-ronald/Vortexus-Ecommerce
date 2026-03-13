import logging
from http import HTTPStatus

from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _normalize_error_details(value):
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalize_error_details(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_error_details(item) for item in value]
    return value


def _extract_detail(data, fallback: str) -> str:
    if isinstance(data, dict):
        detail = data.get('detail')
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if detail:
            return str(detail)
    elif isinstance(data, list) and data:
        first_item = data[0]
        if isinstance(first_item, (str, ErrorDetail)):
            return str(first_item)

    return fallback


def _error_code(exc, response) -> str:
    if isinstance(exc, ValidationError):
        return 'validation_error'

    code = getattr(exc, 'default_code', None)
    if code:
        return str(code)

    try:
        return HTTPStatus(response.status_code).name.lower()
    except ValueError:
        return 'error'


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get('request')
    fallback_detail = HTTPStatus(response.status_code).phrase
    if isinstance(exc, ValidationError):
        detail = 'Request validation failed.'
        errors = _normalize_error_details(response.data)
    else:
        detail = _extract_detail(response.data, fallback_detail)
        errors = None

    payload = {
        'error': {
            'code': _error_code(exc, response),
            'detail': detail,
            'status': response.status_code,
        }
    }
    if errors is not None:
        payload['error']['errors'] = errors

    if request is not None:
        logger.warning(
            'API request failed: method=%s path=%s status=%s code=%s',
            request.method,
            request.get_full_path(),
            response.status_code,
            payload['error']['code'],
        )

    response.data = payload
    return response
