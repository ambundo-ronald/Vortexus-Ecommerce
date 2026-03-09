import logging

from django.contrib.auth import get_user_model
from oscar.apps.customer.auth_backends import EmailBackend as OscarEmailBackend

logger = logging.getLogger(__name__)
User = get_user_model()


class SafeEmailBackend(OscarEmailBackend):
    """
    Prevent duplicate-email collisions from crashing login.

    Oscar raises MultipleObjectsReturned when more than one user matches
    email + password. We treat that as an authentication failure so the
    login form can return a normal error instead of HTTP 500.
    """

    def authenticate(self, *args, **kwargs):
        try:
            return super().authenticate(*args, **kwargs)
        except User.MultipleObjectsReturned:
            submitted_email = kwargs.get("email") or kwargs.get("username")
            logger.warning(
                "Blocked ambiguous login for email '%s': multiple users matched",
                submitted_email,
            )
            return None
