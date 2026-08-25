from django.conf import settings
from django.contrib.sites.models import Site
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.content.models import StorefrontSetting
from apps.notifications.config import configured_from_email, configured_reply_to_email
from apps.payments.services import available_payment_methods

from .account_serializers import AccountProfileUpdateSerializer, AccountSummarySerializer


class AdminStoreSettingsSerializer(serializers.Serializer):
    site_name = serializers.CharField(required=False, allow_blank=False, max_length=100)
    site_domain = serializers.CharField(required=False, allow_blank=False, max_length=100)
    checkout_whatsapp_number = serializers.CharField(required=False, allow_blank=True, max_length=40)

    def validate_site_domain(self, value):
        domain = value.strip().lower().replace('https://', '').replace('http://', '').strip('/')
        if not domain or ' ' in domain:
            raise serializers.ValidationError('Enter a valid site domain.')
        return domain

    def validate_site_name(self, value):
        name = value.strip()
        if len(name) < 2:
            raise serializers.ValidationError('Site name must be at least 2 characters.')
        return name

    def validate_checkout_whatsapp_number(self, value):
        number = value.strip()
        if not number:
            return ''
        normalized = ''.join(ch for ch in number if ch.isdigit() or ch == '+')
        if normalized.count('+') > 1 or ('+' in normalized and not normalized.startswith('+')):
            raise serializers.ValidationError('Enter a valid WhatsApp number, for example +254712345678.')
        digits = ''.join(ch for ch in normalized if ch.isdigit())
        if len(digits) < 8:
            raise serializers.ValidationError('Enter a valid WhatsApp number.')
        return normalized


def _current_site():
    return Site.objects.get_current()


def _serialize_store_settings(site, request=None):
    payment_methods = [
        {
            'code': method.get('code', ''),
            'name': method.get('name', ''),
            'type': method.get('type', ''),
            'requires_prepayment': bool(method.get('requires_prepayment', False)),
            'is_configured': bool(method.get('is_configured', True)),
        }
        for method in available_payment_methods(user=request.user if request and request.user.is_authenticated else None)
    ]
    return {
        'site_name': site.name,
        'site_domain': site.domain,
        'checkout_whatsapp_number': StorefrontSetting.get_value('checkout_whatsapp_number'),
        'default_currency': getattr(settings, 'OSCAR_DEFAULT_CURRENCY', ''),
        'shop_name': getattr(settings, 'OSCAR_SHOP_NAME', ''),
        'support_email': configured_from_email(),
        'reply_to_email': configured_reply_to_email(),
        'payment_methods': payment_methods,
        'async_enabled': bool(getattr(settings, 'ENABLE_ASYNC_TASKS', False)),
        'search_host': getattr(settings, 'OPENSEARCH', {}).get('HOST', ''),
    }


class AdminSettingsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        site = _current_site()
        return Response(
            {
                'store': _serialize_store_settings(site, request=request),
                'profile': AccountSummarySerializer(request.user).data,
                'editable': {
                    'store': ['site_name', 'site_domain', 'checkout_whatsapp_number'],
                    'profile': [
                        'email',
                        'first_name',
                        'last_name',
                        'phone',
                        'company',
                        'country_code',
                        'preferred_currency',
                        'receive_order_updates',
                        'receive_marketing_emails',
                    ],
                },
            }
        )

    def patch(self, request):
        site = _current_site()
        store_payload = request.data.get('store') or {}
        profile_payload = request.data.get('profile') or {}

        if not isinstance(store_payload, dict):
            raise serializers.ValidationError({'store': 'Expected an object.'})
        if not isinstance(profile_payload, dict):
            raise serializers.ValidationError({'profile': 'Expected an object.'})

        previous_store = {
            'site_name': site.name,
            'site_domain': site.domain,
            'checkout_whatsapp_number': StorefrontSetting.get_value('checkout_whatsapp_number'),
        }

        store_serializer = AdminStoreSettingsSerializer(data=store_payload, partial=True)
        store_serializer.is_valid(raise_exception=True)

        profile_serializer = AccountProfileUpdateSerializer(
            instance=request.user,
            data=profile_payload,
            partial=True,
            context={'request': request},
        )
        profile_serializer.is_valid(raise_exception=True)

        dirty_site_fields = []
        if 'site_name' in store_serializer.validated_data and site.name != store_serializer.validated_data['site_name']:
            site.name = store_serializer.validated_data['site_name']
            dirty_site_fields.append('name')
        if 'site_domain' in store_serializer.validated_data and site.domain != store_serializer.validated_data['site_domain']:
            site.domain = store_serializer.validated_data['site_domain']
            dirty_site_fields.append('domain')
        if dirty_site_fields:
            site.save(update_fields=dirty_site_fields)

        if 'checkout_whatsapp_number' in store_serializer.validated_data:
            StorefrontSetting.set_value(
                'checkout_whatsapp_number',
                store_serializer.validated_data['checkout_whatsapp_number'],
                user=request.user,
            )

        user = profile_serializer.save()

        record_audit_event(
            event_type='settings.admin_updated',
            request=request,
            actor=request.user,
            target=request.user,
            message='Admin updated dashboard settings.',
            metadata={
                'store_changed': bool(dirty_site_fields),
                'previous_site_name': previous_store['site_name'],
                'current_site_name': site.name,
                'previous_site_domain': previous_store['site_domain'],
                'current_site_domain': site.domain,
                'previous_checkout_whatsapp_number': previous_store['checkout_whatsapp_number'],
                'current_checkout_whatsapp_number': StorefrontSetting.get_value('checkout_whatsapp_number'),
                'profile_changed': bool(profile_serializer.validated_data),
            },
        )

        return Response(
            {
                'store': _serialize_store_settings(site, request=request),
                'profile': AccountSummarySerializer(user).data,
            }
        )


class PublicStoreSettingsAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        site = _current_site()
        return Response(
            {
                'store': {
                    'site_name': site.name,
                    'site_domain': site.domain,
                    'checkout_whatsapp_number': StorefrontSetting.get_value('checkout_whatsapp_number'),
                    'support_email': configured_from_email(),
                }
            }
        )
