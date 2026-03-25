from __future__ import annotations

from typing import Any

from .models import AuditLog

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
