from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *


ALLOW_INSECURE_PUBLIC_URLS = env.bool('ALLOW_INSECURE_PUBLIC_URLS', default=False)


def _require_public_url(setting_name):
    value = globals().get(setting_name, '')
    parsed = urlparse(value)
    allowed_schemes = {'http', 'https'} if ALLOW_INSECURE_PUBLIC_URLS else {'https'}
    if parsed.scheme not in allowed_schemes or not parsed.netloc:
        protocol = 'HTTP(S)' if ALLOW_INSECURE_PUBLIC_URLS else 'HTTPS'
        raise ImproperlyConfigured(f'{setting_name} must be an absolute {protocol} URL.')
    if not ALLOW_INSECURE_PUBLIC_URLS and parsed.hostname in {'localhost', '127.0.0.1', '0.0.0.0'}:
        raise ImproperlyConfigured(f'{setting_name} cannot point to localhost in production.')


DEBUG = False
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

_require_public_url('STOREFRONT_BASE_URL')
_require_public_url('BACKEND_PUBLIC_BASE_URL')
