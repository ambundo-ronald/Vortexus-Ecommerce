from django.apps import apps
from django.conf import settings
from django.db import OperationalError, ProgrammingError


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
            return config.secret_config.get(key)

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
    if provider == 'mpesa':
        required = [
            get_payment_setting('mpesa', 'consumer_key', ''),
            get_payment_setting('mpesa', 'consumer_secret', ''),
            get_payment_setting('mpesa', 'shortcode', ''),
            get_payment_setting('mpesa', 'passkey', ''),
            get_payment_setting('mpesa', 'callback_url', ''),
        ]
        return all(required)
    if provider == 'pesapal':
        required = [
            get_payment_setting('pesapal', 'consumer_key', ''),
            get_payment_setting('pesapal', 'consumer_secret', ''),
            get_payment_setting('pesapal', 'base_url', ''),
            get_payment_setting('pesapal', 'callback_url', ''),
            get_payment_setting('pesapal', 'ipn_id', ''),
        ]
        return all(required)
    if provider == 'airtel_money':
        return bool(settings.AIRTEL_MONEY_SANDBOX_ENABLED)
    if provider == 'card':
        return bool(settings.CARD_SANDBOX_ENABLED)
    return True
