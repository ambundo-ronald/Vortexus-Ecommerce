from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        profile = getattr(user, 'customer_profile', None)
        verified_at = '' if profile is None else profile.email_verified_at
        return f'{user.pk}{user.password}{user.email}{user.is_active}{verified_at}{timestamp}'


email_verification_token_generator = EmailVerificationTokenGenerator()
