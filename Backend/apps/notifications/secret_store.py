import base64
import hashlib
import hmac
import json
import secrets

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.utils.crypto import constant_time_compare


SECRET_PREFIX = 'sealed:v1:'
_SALT = b'vortexus.notifications.email_configuration'
_NONCE_BYTES = 16


def is_sealed_secret(value: str) -> bool:
    return bool(value and value.startswith(SECRET_PREFIX))


def seal_secret(value: str) -> str:
    if not value or is_sealed_secret(value):
        return value or ''

    nonce = secrets.token_bytes(_NONCE_BYTES)
    payload = value.encode('utf-8')
    ciphertext = _xor_bytes(payload, _key_stream(nonce, len(payload)))
    tag = hmac.new(_signing_key(), nonce + ciphertext, hashlib.sha256).digest()
    envelope = {
        'n': _b64encode(nonce),
        'c': _b64encode(ciphertext),
        't': _b64encode(tag),
    }
    return SECRET_PREFIX + _b64encode(json.dumps(envelope, separators=(',', ':')).encode('utf-8'))


def unseal_secret(value: str) -> str:
    if not value:
        return ''
    if not is_sealed_secret(value):
        return value

    try:
        envelope = json.loads(_b64decode(value[len(SECRET_PREFIX) :]).decode('utf-8'))
        nonce = _b64decode(envelope['n'])
        ciphertext = _b64decode(envelope['c'])
        expected_tag = _b64decode(envelope['t'])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SuspiciousOperation('Stored email secret is malformed.') from exc

    actual_tag = hmac.new(_signing_key(), nonce + ciphertext, hashlib.sha256).digest()
    if not constant_time_compare(actual_tag, expected_tag):
        raise SuspiciousOperation('Stored email secret failed integrity validation.')

    return _xor_bytes(ciphertext, _key_stream(nonce, len(ciphertext))).decode('utf-8')


def _secret_material() -> bytes:
    value = getattr(settings, 'EMAIL_SECRET_KEY', '') or settings.SECRET_KEY
    if not value:
        raise ImproperlyConfigured('EMAIL_SECRET_KEY or SECRET_KEY must be configured before sealing email secrets.')
    return str(value).encode('utf-8')


def _signing_key() -> bytes:
    return hashlib.pbkdf2_hmac('sha256', _secret_material(), _SALT + b':signing', 200_000, dklen=32)


def _cipher_key() -> bytes:
    return hashlib.pbkdf2_hmac('sha256', _secret_material(), _SALT + b':cipher', 200_000, dklen=32)


def _key_stream(nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    key = _cipher_key()
    while sum(len(block) for block in blocks) < length:
        counter_bytes = counter.to_bytes(4, 'big')
        blocks.append(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())
        counter += 1
    return b''.join(blocks)[:length]


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def _b64decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('ascii'))
