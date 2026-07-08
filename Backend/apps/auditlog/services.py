from __future__ import annotations

import hashlib
from typing import Any

from django.conf import settings

from .models import AuditLog, SearchAnalyticsEvent

SENSITIVE_METADATA_KEYS = (
    'api_key',
    'api_secret',
    'secret',
    'password',
    'token',
    'authorization',
)


def _actor_role(user) -> str:
    if not user or not getattr(user, 'is_authenticated', False):
        return 'anonymous'
    if getattr(user, 'is_superuser', False):
        return 'superuser'
    if getattr(user, 'is_staff', False):
        return 'staff'
    if hasattr(user, 'supplier_profile'):
        return 'supplier'
    return 'customer'


def _request_ip(request) -> str | None:
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _target_details(target) -> dict[str, str]:
    if target is None:
        return {'target_type': '', 'target_id': '', 'target_repr': ''}
    meta = getattr(target, '_meta', None)
    target_type = f'{meta.app_label}.{meta.model_name}' if meta else target.__class__.__name__.lower()
    target_id = str(getattr(target, 'pk', '') or '')
    target_repr = str(target)[:255]
    return {'target_type': target_type, 'target_id': target_id, 'target_repr': target_repr}


def sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_str = str(key).lower()
            if any(sensitive in key_str for sensitive in SENSITIVE_METADATA_KEYS):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_metadata(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_metadata(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_metadata(item) for item in value]
    return value


def record_audit_event(
    *,
    event_type: str,
    request=None,
    actor=None,
    target=None,
    status: str = AuditLog.STATUS_SUCCESS,
    message: str = '',
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    actor = actor or getattr(request, 'user', None)
    actor_email = ''
    if actor and getattr(actor, 'is_authenticated', False):
        actor_email = getattr(actor, 'email', '') or getattr(actor, 'username', '') or ''

    target_details = _target_details(target)
    return AuditLog.objects.create(
        event_type=event_type,
        status=status,
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        actor_email=actor_email,
        actor_role=_actor_role(actor),
        request_method=getattr(request, 'method', '') if request is not None else '',
        path=getattr(request, 'path', '')[:255] if request is not None else '',
        ip_address=_request_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '') if request is not None else '')[:255],
        target_type=target_details['target_type'],
        target_id=target_details['target_id'],
        target_repr=target_details['target_repr'],
        message=message[:255],
        metadata=sanitize_metadata(metadata or {}),
    )


SEARCH_ANALYTICS_EVENT_MAP = {
    'storefront.search_submitted': SearchAnalyticsEvent.EVENT_SEARCH_SUBMITTED,
    'storefront.search_results_viewed': SearchAnalyticsEvent.EVENT_RESULTS_VIEWED,
    'storefront.search_no_results': SearchAnalyticsEvent.EVENT_NO_RESULTS,
    'storefront.suggestion_clicked': SearchAnalyticsEvent.EVENT_SUGGESTION_CLICKED,
    'storefront.product_clicked': SearchAnalyticsEvent.EVENT_PRODUCT_CLICKED,
    'storefront.image_search_submitted': SearchAnalyticsEvent.EVENT_IMAGE_SEARCH_SUBMITTED,
    'storefront.cart_item_added': SearchAnalyticsEvent.EVENT_CART_ADDED,
    'storefront.order_confirmation_viewed': SearchAnalyticsEvent.EVENT_ORDER_CONVERTED,
}


def _safe_int(value) -> int | None:
    if value in ('', None):
        return None
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return None


def _hash_ip(ip: str | None) -> str:
    if not ip:
        return ''
    salt = getattr(settings, 'SECRET_KEY', '')
    return hashlib.sha256(f'{salt}:{ip}'.encode('utf-8')).hexdigest()


def record_search_analytics_event(*, event_type: str, request=None, metadata: dict[str, Any] | None = None) -> SearchAnalyticsEvent | None:
    mapped_event = SEARCH_ANALYTICS_EVENT_MAP.get(event_type)
    if not mapped_event:
        return None

    metadata = sanitize_metadata(metadata or {})
    actor = getattr(request, 'user', None)
    user = actor if getattr(actor, 'is_authenticated', False) else None
    query = str(metadata.get('search') or metadata.get('query') or '').strip()
    source = str(metadata.get('source') or '').strip()
    if not source:
        if mapped_event == SearchAnalyticsEvent.EVENT_IMAGE_SEARCH_SUBMITTED:
            source = SearchAnalyticsEvent.SOURCE_IMAGE
        elif mapped_event == SearchAnalyticsEvent.EVENT_ORDER_CONVERTED:
            source = SearchAnalyticsEvent.SOURCE_ORDER
        elif mapped_event == SearchAnalyticsEvent.EVENT_CART_ADDED:
            source = SearchAnalyticsEvent.SOURCE_CART
        elif mapped_event == SearchAnalyticsEvent.EVENT_PRODUCT_CLICKED:
            source = SearchAnalyticsEvent.SOURCE_PRODUCT
        else:
            source = SearchAnalyticsEvent.SOURCE_TEXT

    return SearchAnalyticsEvent.objects.create(
        event_type=mapped_event,
        source=source[:40],
        query=query[:255],
        search_context_id=str(metadata.get('search_context_id') or '')[:64],
        anonymous_id=str(metadata.get('anonymous_id') or '')[:64],
        user=user,
        user_email=(getattr(user, 'email', '') or getattr(user, 'username', '') or '')[:254] if user else '',
        category=str(metadata.get('category') or '')[:120],
        brand=str(metadata.get('brand') or '')[:120],
        result_count=_safe_int(metadata.get('result_count')),
        product_id=_safe_int(metadata.get('product_id')),
        product_title=str(metadata.get('product_title') or metadata.get('title') or '')[:255],
        order_number=str(metadata.get('order_number') or '')[:64],
        path=(getattr(request, 'path', '') if request is not None else str(metadata.get('path') or ''))[:255],
        ip_hash=_hash_ip(_request_ip(request)),
        user_agent=(request.META.get('HTTP_USER_AGENT', '') if request is not None else '')[:255],
        metadata=metadata,
    )
