from rest_framework.response import Response


def api_error(code: str, detail: str, *, status_code: int = 400, errors=None, extra=None) -> Response:
    payload = {
        'error': {
            'code': code,
            'detail': detail,
            'status': status_code,
        }
    }
    if errors:
        payload['error']['errors'] = errors
    if extra:
        payload['error'].update(extra)
    return Response(payload, status=status_code)


def validation_error(detail: str, *, errors=None) -> Response:
    return api_error('validation_error', detail, status_code=400, errors=errors)
