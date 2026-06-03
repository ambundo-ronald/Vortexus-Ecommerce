from django.apps import apps
from django.conf import settings
from django.core.mail import get_connection
from django.db import OperationalError, ProgrammingError


def get_email_configuration():
    EmailConfiguration = apps.get_model('notifications', 'EmailConfiguration')
    try:
        return EmailConfiguration.objects.filter(provider='smtp').first()
    except (OperationalError, ProgrammingError):
        return None


def configured_email_backend() -> str:
    config = get_email_configuration()
    if config and config.is_enabled and config.host:
        return 'django.core.mail.backends.smtp.EmailBackend'
    return settings.EMAIL_BACKEND


def configured_from_email() -> str:
    config = get_email_configuration()
    if config and config.is_enabled and config.from_email:
        return config.from_email
    return settings.DEFAULT_FROM_EMAIL


def configured_reply_to_email() -> str:
    config = get_email_configuration()
    if config and config.is_enabled and config.reply_to_email:
        return config.reply_to_email
    return settings.NOTIFICATION_REPLY_TO_EMAIL


def configured_sales_recipients() -> list[str]:
    config = get_email_configuration()
    if config and config.is_enabled and config.sales_recipients:
        return [
            recipient.strip()
            for recipient in config.sales_recipients.replace(';', ',').split(',')
            if recipient.strip()
        ]
    return list(settings.SALES_NOTIFICATION_RECIPIENTS)


def build_email_connection(fail_silently: bool = False):
    config = get_email_configuration()
    if not (config and config.is_enabled and config.host):
        return get_connection(fail_silently=fail_silently)

    return get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=config.host,
        port=config.port,
        username=config.username or None,
        password=config.get_password_secret() or None,
        use_tls=config.use_tls,
        use_ssl=config.use_ssl,
        timeout=config.timeout_seconds,
        fail_silently=fail_silently,
    )


def email_configured_for_delivery() -> bool:
    config = get_email_configuration()
    if not config:
        return False
    return bool(config.is_enabled and config.host and config.from_email)
