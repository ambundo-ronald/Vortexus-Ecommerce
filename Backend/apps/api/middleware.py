import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


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
