from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    timeout_setting_name = 'EMAIL_VERIFICATION_TIMEOUT_SECONDS'

    def _make_hash_value(self, user, timestamp):
        profile = getattr(user, 'customer_profile', None)
        verified_at = '' if profile is None else profile.email_verified_at
        return f'{user.pk}{user.password}{user.email}{user.is_active}{verified_at}{timestamp}'

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False
        try:
            timestamp = base36_to_int(token.split('-', 1)[0])
        except (IndexError, ValueError):
            return False
        timeout_seconds = getattr(settings, self.timeout_setting_name, 30 * 60)
        return (self._num_seconds(self._now()) - timestamp) <= timeout_seconds


email_verification_token_generator = EmailVerificationTokenGenerator()
