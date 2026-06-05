from django.apps import apps
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db import OperationalError, ProgrammingError

from apps.notifications.secret_store import unseal_secret


PROVIDER_SETTINGS = {
    'mpesa': {
        'public': {
            'base_url': 'MPESA_BASE_URL',
            'shortcode': 'MPESA_SHORTCODE',
            'callback_url': 'MPESA_CALLBACK_URL',
            'transaction_type': 'MPESA_TRANSACTION_TYPE',
            'timeout_seconds': 'MPESA_TIMEOUT_SECONDS',
        },
        'secret': {
            'consumer_key': 'MPESA_CONSUMER_KEY',
            'consumer_secret': 'MPESA_CONSUMER_SECRET',
            'passkey': 'MPESA_PASSKEY',
        },
    },
    'pesapal': {
        'public': {
            'base_url': 'PESAPAL_BASE_URL',
            'callback_url': 'PESAPAL_CALLBACK_URL',
            'cancellation_url': 'PESAPAL_CANCELLATION_URL',
            'ipn_url': 'PESAPAL_IPN_URL',
            'ipn_id': 'PESAPAL_IPN_ID',
            'notification_type': 'PESAPAL_IPN_NOTIFICATION_TYPE',
            'branch': 'PESAPAL_BRANCH',
            'redirect_mode': 'PESAPAL_REDIRECT_MODE',
            'timeout_seconds': 'PESAPAL_TIMEOUT_SECONDS',
        },
        'secret': {
            'consumer_key': 'PESAPAL_CONSUMER_KEY',
            'consumer_secret': 'PESAPAL_CONSUMER_SECRET',
        },
    },
    'airtel_money': {
        'public': {
            'provider_name': 'AIRTEL_MONEY_PROVIDER_NAME',
        },
        'secret': {},
    },
    'card': {
        'public': {
            'provider_name': 'CARD_PROVIDER_NAME',
        },
        'secret': {},
    },
}


def get_provider_config(provider: str):
    PaymentProviderConfiguration = apps.get_model('payments', 'PaymentProviderConfiguration')
    try:
        return PaymentProviderConfiguration.objects.filter(provider=provider).first()
    except (OperationalError, ProgrammingError):
        return None


def provider_is_enabled(provider: str, default: bool = True) -> bool:
    config = get_provider_config(provider)
    if config is None:
        return default
    return bool(config.is_enabled)


def get_payment_setting(provider: str, key: str, default=None):
    config = get_provider_config(provider)
    if config:
        if key in (config.public_config or {}):
            return config.public_config.get(key)
        if key in (config.secret_config or {}):
            try:
                return unseal_secret(config.secret_config.get(key) or '')
            except SuspiciousOperation:
                return default

    setting_name = PROVIDER_SETTINGS.get(provider, {}).get('public', {}).get(key)
    if not setting_name:
        setting_name = PROVIDER_SETTINGS.get(provider, {}).get('secret', {}).get(key)
    if not setting_name:
        return default

    return getattr(settings, setting_name, default)


def has_payment_secret(provider: str, key: str) -> bool:
    value = get_payment_setting(provider, key, '')
    return bool(value)


def provider_is_configured(provider: str) -> bool:
    return not provider_missing_requirements(provider)


def provider_missing_requirements(provider: str) -> list[str]:
    if provider == 'mpesa':
        required = {
            'consumer_key': get_payment_setting('mpesa', 'consumer_key', ''),
            'consumer_secret': get_payment_setting('mpesa', 'consumer_secret', ''),
            'shortcode': get_payment_setting('mpesa', 'shortcode', ''),
            'passkey': get_payment_setting('mpesa', 'passkey', ''),
            'callback_url': get_payment_setting('mpesa', 'callback_url', ''),
        }
        return [key for key, value in required.items() if not value]
    if provider == 'pesapal':
        required = {
            'consumer_key': get_payment_setting('pesapal', 'consumer_key', ''),
            'consumer_secret': get_payment_setting('pesapal', 'consumer_secret', ''),
            'base_url': get_payment_setting('pesapal', 'base_url', ''),
            'callback_url': get_payment_setting('pesapal', 'callback_url', ''),
            'ipn_id': get_payment_setting('pesapal', 'ipn_id', ''),
        }
        return [key for key, value in required.items() if not value]
    if provider == 'airtel_money':
        return [] if settings.AIRTEL_MONEY_SANDBOX_ENABLED else ['sandbox_enabled']
    if provider == 'card':
        return [] if settings.CARD_SANDBOX_ENABLED else ['sandbox_enabled']
    return []
