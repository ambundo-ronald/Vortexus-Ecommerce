from django.apps import apps
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.db import transaction
from django.db.models import Q
from django.template.defaultfilters import slugify
from rest_framework import serializers
from rest_framework.exceptions import APIException, AuthenticationFailed

from apps.common.currency import (
    currency_for_country,
    display_currency_for_user,
    is_supported_currency,
    normalize_country_code,
    normalize_currency_code,
)

User = get_user_model()


class AccountInactive(APIException):
    status_code = 403
    default_detail = (
        'This account was deactivated. Request reactivation from support, then sign in once the account is restored.'
    )
    default_code = 'account_inactive'


def get_or_create_customer_profile(user):
    CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def get_supplier_profile(user):
    return getattr(user, 'supplier_profile', None)


class AccountSummarySerializer(serializers.Serializer):
    def to_representation(self, user):
        profile = get_or_create_customer_profile(user)
        supplier_profile = get_supplier_profile(user)
        full_name = ' '.join(part for part in [user.first_name, user.last_name] if part).strip()
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': full_name,
            'phone': profile.phone,
            'company': profile.company,
            'country_code': profile.country_code,
            'preferred_currency': profile.preferred_currency,
            'display_currency': display_currency_for_user(user),
            'settings': {
                'receive_order_updates': profile.receive_order_updates,
                'receive_marketing_emails': profile.receive_marketing_emails,
                'two_factor_email_enabled': profile.two_factor_email_enabled,
            },
            'email_verification': {
                'is_verified': profile.email_verified_at is not None,
                'verified_at': profile.email_verified_at,
            },
            'supplier': {
                'is_supplier': supplier_profile is not None,
                'status': supplier_profile.status if supplier_profile else '',
                'company_name': supplier_profile.company_name if supplier_profile else '',
                'partner_id': supplier_profile.partner_id if supplier_profile else None,
            },
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'dashboard_role': 'platform_admin' if user.is_superuser else 'account_manager' if user.is_staff else 'supplier' if supplier_profile else 'customer',
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        }


class AccountRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    country_code = serializers.CharField(required=False, allow_blank=True, max_length=2)
    preferred_currency = serializers.CharField(required=False, allow_blank=True, max_length=3)
    receive_order_updates = serializers.BooleanField(required=False, default=True)
    receive_marketing_emails = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        existing_user = User.objects.filter(email__iexact=value).first()
        if existing_user and not existing_user.is_active:
            raise serializers.ValidationError(
                'This email belongs to a deactivated account. Request reactivation before signing in or registering again.'
            )
        if existing_user:
            raise serializers.ValidationError('An account with this email already exists.')
        return value.strip().lower()

    def validate_country_code(self, value):
        normalized = normalize_country_code(value)
        if normalized and currency_for_country(normalized) is None:
            raise serializers.ValidationError('Unsupported country code.')
        return normalized

    def validate_preferred_currency(self, value):
        normalized = normalize_currency_code(value)
        if normalized and not is_supported_currency(normalized):
            raise serializers.ValidationError('Unsupported currency.')
        return normalized

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')
        if password != password_confirm:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        password_validation.validate_password(password)

        country_code = attrs.get('country_code', '')
        if country_code and not attrs.get('preferred_currency'):
            attrs['preferred_currency'] = currency_for_country(country_code) or ''
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email'].strip().lower()
        user = User.objects.create_user(
            username=self._generate_username(email),
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '').strip(),
            last_name=validated_data.get('last_name', '').strip(),
        )

        profile = get_or_create_customer_profile(user)
        profile.phone = validated_data.get('phone', '').strip()
        profile.company = validated_data.get('company', '').strip()
        profile.country_code = validated_data.get('country_code', '')
        profile.preferred_currency = validated_data.get('preferred_currency', '')
        profile.receive_order_updates = validated_data.get('receive_order_updates', True)
        profile.receive_marketing_emails = validated_data.get('receive_marketing_emails', False)
        profile.save()

        return user

    def _generate_username(self, email: str) -> str:
        base = slugify(email.split('@', 1)[0]).replace('-', '_')[:120] or 'user'
        candidate = base
        suffix = 1
        while User.objects.filter(username__iexact=candidate).exists():
            suffix += 1
            candidate = f'{base[:140]}_{suffix}'
        return candidate[:150]


class AccountLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})

    def validate(self, attrs):
        request = self.context.get('request')
        identifier = attrs['identifier'].strip()
        password = attrs['password']

        user = authenticate(request=request, username=identifier, password=password)
        if user is None:
            user = authenticate(request=request, email=identifier, password=password)

        if user is None:
            inactive_user = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
            if inactive_user and not inactive_user.is_active and inactive_user.check_password(password):
                raise AccountInactive()
            raise AuthenticationFailed('Invalid credentials.')
        if not user.is_active:
            raise AccountInactive()

        attrs['user'] = user
        return attrs


class AccountReactivationRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)

    def validate_identifier(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        identifier = attrs['identifier']
        user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        attrs['inactive_user'] = user if user and not user.is_active else None
        return attrs


class AccountProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    country_code = serializers.CharField(required=False, allow_blank=True, max_length=2)
    preferred_currency = serializers.CharField(required=False, allow_blank=True, max_length=3)
    receive_order_updates = serializers.BooleanField(required=False)
    receive_marketing_emails = serializers.BooleanField(required=False)
    two_factor_email_enabled = serializers.BooleanField(required=False)

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Another account already uses this email.')
        return value.strip().lower()

    def validate_country_code(self, value):
        normalized = normalize_country_code(value)
        if normalized and currency_for_country(normalized) is None:
            raise serializers.ValidationError('Unsupported country code.')
        return normalized

    def validate_preferred_currency(self, value):
        normalized = normalize_currency_code(value)
        if normalized and not is_supported_currency(normalized):
            raise serializers.ValidationError('Unsupported currency.')
        return normalized

    def validate(self, attrs):
        user = self.context['request'].user
        profile = get_or_create_customer_profile(user)
        if attrs.get('two_factor_email_enabled') and profile.email_verified_at is None:
            raise serializers.ValidationError({'two_factor_email_enabled': 'Verify your email before enabling email 2FA.'})
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        profile = get_or_create_customer_profile(instance)
        user_dirty_fields = []
        profile_dirty_fields = []

        for field in ('email', 'first_name', 'last_name'):
            if field in validated_data:
                new_value = validated_data[field].strip() if isinstance(validated_data[field], str) else validated_data[field]
                if getattr(instance, field) != new_value:
                    setattr(instance, field, new_value)
                    user_dirty_fields.append(field)
                    if field == 'email' and profile.email_verified_at is not None:
                        profile.email_verified_at = None
                        profile_dirty_fields.append('email_verified_at')
                    if field == 'email' and profile.two_factor_email_enabled:
                        profile.two_factor_email_enabled = False
                        profile_dirty_fields.append('two_factor_email_enabled')

        for field in ('phone', 'company'):
            if field in validated_data:
                new_value = validated_data[field].strip()
                if getattr(profile, field) != new_value:
                    setattr(profile, field, new_value)
                    profile_dirty_fields.append(field)

        if 'country_code' in validated_data:
            country_code = validated_data['country_code']
            if profile.country_code != country_code:
                profile.country_code = country_code
                profile_dirty_fields.append('country_code')
            if 'preferred_currency' not in validated_data and not profile.preferred_currency:
                derived_currency = currency_for_country(country_code) or ''
                if profile.preferred_currency != derived_currency:
                    profile.preferred_currency = derived_currency
                    profile_dirty_fields.append('preferred_currency')

        if 'preferred_currency' in validated_data:
            preferred_currency = validated_data['preferred_currency']
            if profile.preferred_currency != preferred_currency:
                profile.preferred_currency = preferred_currency
                profile_dirty_fields.append('preferred_currency')

        for field in ('receive_order_updates', 'receive_marketing_emails', 'two_factor_email_enabled'):
            if field in validated_data and getattr(profile, field) != validated_data[field]:
                setattr(profile, field, validated_data[field])
                profile_dirty_fields.append(field)

        if user_dirty_fields:
            instance.save(update_fields=user_dirty_fields)
        if profile_dirty_fields:
            profile.save(update_fields=profile_dirty_fields)

        return instance


class AccountPasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False, style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})

        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})

        password_validation.validate_password(attrs['new_password'], user=user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
