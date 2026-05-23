from django.conf import settings
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.payments.config import get_payment_setting, has_payment_secret, provider_is_configured, provider_is_enabled
from apps.payments.models import PaymentProviderConfiguration


class MpesaConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    base_url = serializers.URLField(required=False, allow_blank=True)
    consumer_key = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    consumer_secret = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    shortcode = serializers.CharField(required=False, allow_blank=True, max_length=40)
    passkey = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=255)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    transaction_type = serializers.CharField(required=False, allow_blank=True, max_length=80)
    timeout_seconds = serializers.IntegerField(required=False, min_value=1, max_value=120)


class AirtelMoneyConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    provider_name = serializers.CharField(required=False, allow_blank=True, max_length=80)


class CardConfigSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(required=False)
    provider_name = serializers.CharField(required=False, allow_blank=True, max_length=80)


def _serialize_provider(provider: str) -> dict:
    if provider == 'mpesa':
        return {
            'is_enabled': provider_is_enabled('mpesa', default=True),
            'is_configured': provider_is_configured('mpesa'),
            'base_url': get_payment_setting('mpesa', 'base_url', settings.MPESA_BASE_URL),
            'has_consumer_key': has_payment_secret('mpesa', 'consumer_key'),
            'has_consumer_secret': has_payment_secret('mpesa', 'consumer_secret'),
            'shortcode': get_payment_setting('mpesa', 'shortcode', settings.MPESA_SHORTCODE),
            'has_passkey': has_payment_secret('mpesa', 'passkey'),
            'callback_url': get_payment_setting('mpesa', 'callback_url', settings.MPESA_CALLBACK_URL),
            'transaction_type': get_payment_setting('mpesa', 'transaction_type', settings.MPESA_TRANSACTION_TYPE),
            'timeout_seconds': int(get_payment_setting('mpesa', 'timeout_seconds', settings.MPESA_TIMEOUT_SECONDS)),
        }
    if provider == 'airtel_money':
        return {
            'is_enabled': provider_is_enabled('airtel_money', default=True),
            'is_configured': bool(provider_is_configured('airtel_money') and provider_is_enabled('airtel_money', default=True)),
            'provider_name': get_payment_setting('airtel_money', 'provider_name', settings.AIRTEL_MONEY_PROVIDER_NAME),
            'sandbox_enabled': bool(settings.AIRTEL_MONEY_SANDBOX_ENABLED),
        }
    return {
        'is_enabled': provider_is_enabled('card', default=True),
        'is_configured': bool(provider_is_configured('card') and provider_is_enabled('card', default=True)),
        'provider_name': get_payment_setting('card', 'provider_name', settings.CARD_PROVIDER_NAME),
        'sandbox_enabled': bool(settings.CARD_SANDBOX_ENABLED),
    }


def _upsert_provider(provider: str, *, is_enabled: bool | None, public_config: dict, secret_config: dict, user):
    config, _ = PaymentProviderConfiguration.objects.get_or_create(provider=provider)
    if is_enabled is not None:
        config.is_enabled = is_enabled

    next_public = config.public_config.copy()
    for key, value in public_config.items():
        next_public[key] = value
    config.public_config = next_public

    next_secret = config.secret_config.copy()
    for key, value in secret_config.items():
        if value:
            next_secret[key] = value
    config.secret_config = next_secret
    config.updated_by = user
    config.save()
    return config


class AdminPaymentConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(
            {
                'mpesa': _serialize_provider('mpesa'),
                'airtel_money': _serialize_provider('airtel_money'),
                'card': _serialize_provider('card'),
            }
        )

    def patch(self, request):
        changed = []

        if 'mpesa' in request.data:
            serializer = MpesaConfigSerializer(data=request.data.get('mpesa') or {}, partial=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            _upsert_provider(
                'mpesa',
                is_enabled=data.get('is_enabled'),
                public_config={
                    key: data[key]
                    for key in ['base_url', 'shortcode', 'callback_url', 'transaction_type', 'timeout_seconds']
                    if key in data
                },
                secret_config={
                    key: data[key]
                    for key in ['consumer_key', 'consumer_secret', 'passkey']
                    if key in data
                },
                user=request.user,
            )
            changed.append('mpesa')

        if 'airtel_money' in request.data:
            serializer = AirtelMoneyConfigSerializer(data=request.data.get('airtel_money') or {}, partial=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            _upsert_provider(
                'airtel_money',
                is_enabled=data.get('is_enabled'),
                public_config={key: data[key] for key in ['provider_name'] if key in data},
                secret_config={},
                user=request.user,
            )
            changed.append('airtel_money')

        if 'card' in request.data:
            serializer = CardConfigSerializer(data=request.data.get('card') or {}, partial=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            _upsert_provider(
                'card',
                is_enabled=data.get('is_enabled'),
                public_config={key: data[key] for key in ['provider_name'] if key in data},
                secret_config={},
                user=request.user,
            )
            changed.append('card')

        if changed:
            record_audit_event(
                event_type='payments.configuration_updated',
                request=request,
                actor=request.user,
                target=request.user,
                message='Payment provider configuration updated.',
                metadata={'providers': changed},
            )

        return Response(
            {
                'mpesa': _serialize_provider('mpesa'),
                'airtel_money': _serialize_provider('airtel_money'),
                'card': _serialize_provider('card'),
            }
        )
