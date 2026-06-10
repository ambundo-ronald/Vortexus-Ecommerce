from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, override_settings

from .services import build_email_verification_url, build_password_reset_url


@override_settings(STOREFRONT_BASE_URL='https://shop.example.com')
class StorefrontEmailLinkTests(SimpleTestCase):
    def setUp(self):
        self.user = get_user_model()(
            pk=42,
            email='customer@example.com',
            username='customer@example.com',
        )
        self.user.set_password('Test-password-123')
        self.user._state.fields_cache['customer_profile'] = SimpleNamespace(email_verified_at=None)

    def test_email_verification_link_uses_configured_storefront(self):
        parsed = urlparse(build_email_verification_url(self.user))
        query = parse_qs(parsed.query)

        self.assertEqual(f'{parsed.scheme}://{parsed.netloc}{parsed.path}', 'https://shop.example.com/account/verify-email')
        self.assertTrue(query['uid'][0])
        self.assertTrue(query['token'][0])

    def test_password_reset_link_uses_configured_storefront(self):
        parsed = urlparse(build_password_reset_url(self.user))
        query = parse_qs(parsed.query)

        self.assertEqual(f'{parsed.scheme}://{parsed.netloc}{parsed.path}', 'https://shop.example.com/reset-password')
        self.assertTrue(query['uid'][0])
        self.assertTrue(query['token'][0])
