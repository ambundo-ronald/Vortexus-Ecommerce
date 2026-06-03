import secrets
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac


TWO_FACTOR_CODE_TTL_MINUTES = 10
TWO_FACTOR_MAX_ATTEMPTS = 5


def generate_two_factor_code() -> str:
    return f'{secrets.randbelow(1_000_000):06d}'


def hash_two_factor_code(code: str) -> str:
    return salted_hmac('accounts.email_two_factor', code.strip(), secret=settings.SECRET_KEY).hexdigest()


def create_email_two_factor_challenge(user, code: str):
    Challenge = apps.get_model('accounts', 'EmailTwoFactorChallenge')
    return Challenge.objects.create(
        user=user,
        code_hash=hash_two_factor_code(code),
        expires_at=timezone.now() + timedelta(minutes=TWO_FACTOR_CODE_TTL_MINUTES),
    )


def verify_email_two_factor_challenge(challenge, code: str) -> tuple[bool, str]:
    now = timezone.now()
    if challenge.consumed_at is not None:
        return False, 'This code has already been used.'
    if challenge.expires_at <= now:
        return False, 'This code has expired.'
    if challenge.attempts >= TWO_FACTOR_MAX_ATTEMPTS:
        return False, 'Too many attempts. Please sign in again.'

    challenge.attempts += 1
    if not constant_time_compare(challenge.code_hash, hash_two_factor_code(code)):
        challenge.save(update_fields=['attempts'])
        return False, 'Invalid verification code.'

    challenge.consumed_at = now
    challenge.save(update_fields=['attempts', 'consumed_at'])
    return True, ''
