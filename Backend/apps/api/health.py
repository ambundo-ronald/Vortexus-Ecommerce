from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db import connections

from apps.common.clients import get_opensearch_client


def _database_health() -> dict:
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'error', 'detail': str(exc)}


def _cache_health() -> dict:
    try:
        cache_key = 'healthcheck:cache'
        cache.set(cache_key, 'ok', timeout=10)
        result = cache.get(cache_key)
        if result != 'ok':
            raise RuntimeError('Cache round-trip failed.')
        return {'status': 'ok', 'backend': settings.CACHES['default']['BACKEND']}
    except Exception as exc:
        return {'status': 'error', 'detail': str(exc)}


def _opensearch_health() -> dict:
    try:
        client = get_opensearch_client()
        return {'status': 'ok' if client.ping() else 'error', 'host': settings.OPENSEARCH['HOST']}
    except Exception as exc:
        return {'status': 'error', 'host': settings.OPENSEARCH['HOST'], 'detail': str(exc)}


def _celery_health() -> dict:
    enabled = bool(getattr(settings, 'ENABLE_ASYNC_TASKS', False))
    broker = getattr(settings, 'CELERY_BROKER_URL', '')
    if not enabled:
        return {'status': 'disabled', 'broker': broker}
    return {'status': 'configured', 'broker': broker}


def _media_storage_health() -> dict:
    media_root = settings.MEDIA_ROOT
    try:
        media_root.mkdir(parents=True, exist_ok=True)
        probe = media_root / '.healthcheck'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        return {'status': 'ok', 'media_root': str(media_root), 'media_url': settings.MEDIA_URL}
    except Exception as exc:
        return {'status': 'error', 'media_root': str(media_root), 'media_url': settings.MEDIA_URL, 'detail': str(exc)}


def readiness_payload() -> dict:
    checks = {
        'database': _database_health(),
        'cache': _cache_health(),
        'media_storage': _media_storage_health(),
        'opensearch': _opensearch_health(),
        'celery': _celery_health(),
    }
    required_failures = [name for name in ('database', 'cache', 'media_storage') if checks[name]['status'] != 'ok']
    optional_failures = [name for name in ('opensearch',) if checks[name]['status'] != 'ok']

    if required_failures:
        overall = 'unhealthy'
    elif optional_failures:
        overall = 'degraded'
    else:
        overall = 'healthy'

    return {
        'status': overall,
        'service': 'vortexus-backend',
        'checks': checks,
        'async_enabled': bool(getattr(settings, 'ENABLE_ASYNC_TASKS', False)),
        'debug': bool(getattr(settings, 'DEBUG', False)),
    }
