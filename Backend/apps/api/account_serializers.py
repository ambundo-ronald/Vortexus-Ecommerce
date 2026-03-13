from django.apps import apps
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.db import transaction
from django.template.defaultfilters import slugify
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def get_or_create_customer_profile(user):
    CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


class AccountSummarySerializer(serializers.Serializer):
    def to_representation(self, user):
        profile = get_or_create_customer_profile(user)
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
            'settings': {
                'receive_order_updates': profile.receive_order_updates,
                'receive_marketing_emails': profile.receive_marketing_emails,
            },
            'is_staff': user.is_staff,
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
    receive_order_updates = serializers.BooleanField(required=False, default=True)
    receive_marketing_emails = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')
        if password != password_confirm:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        password_validation.validate_password(password)
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
            raise AuthenticationFailed('Invalid credentials.')
        if not user.is_active:
            raise AuthenticationFailed('This account is inactive.')

        attrs['user'] = user
        return attrs


class AccountProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    receive_order_updates = serializers.BooleanField(required=False)
    receive_marketing_emails = serializers.BooleanField(required=False)

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Another account already uses this email.')
        return value.strip().lower()

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

        for field in ('phone', 'company'):
            if field in validated_data:
                new_value = validated_data[field].strip()
                if getattr(profile, field) != new_value:
                    setattr(profile, field, new_value)
                    profile_dirty_fields.append(field)

        for field in ('receive_order_updates', 'receive_marketing_emails'):
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
