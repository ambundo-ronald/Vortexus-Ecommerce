import logging
import time

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ApiRequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/api/'):
            request._api_request_started_at = time.perf_counter()
        return None

    def process_response(self, request, response):
        if not request.path.startswith('/api/'):
            return response

        started_at = getattr(request, '_api_request_started_at', None)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2) if started_at else None
        logger.info(
            'api_request method=%s path=%s status=%s duration_ms=%s user_id=%s',
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
            getattr(getattr(request, 'user', None), 'id', None),
        )
        return response


class ApiExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if not request.path.startswith('/api/'):
            return None

        logger.exception(
            'Unhandled API exception: method=%s path=%s',
            request.method,
            request.get_full_path(),
        )

        payload = {
            'error': {
                'code': 'internal_server_error',
                'detail': 'An unexpected error occurred.',
                'status': 500,
            }
        }

        if settings.DEBUG:
            payload['error']['debug'] = str(exception) or exception.__class__.__name__

        return JsonResponse(payload, status=500)
