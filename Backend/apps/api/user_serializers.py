from django.contrib.auth import get_user_model, password_validation
from django.db import transaction
from rest_framework import serializers

from .account_serializers import get_or_create_customer_profile

User = get_user_model()

ADMIN_USER_ROLE_CHOICES = [
    ('customer', 'Customer'),
    ('staff', 'Staff'),
    ('admin', 'Admin'),
]


def _admin_user_role(user) -> str:
    if getattr(user, 'is_superuser', False):
        return 'Admin'
    if getattr(user, 'is_staff', False):
        return 'Staff'
    if hasattr(user, 'supplier_profile'):
        return 'Supplier'
    return 'Customer'


def _admin_user_status(user) -> str:
    return 'Active' if getattr(user, 'is_active', False) else 'Suspended'


def _admin_user_name(user) -> str:
    full_name = ' '.join(part for part in [user.first_name, user.last_name] if part).strip()
    return full_name or user.username or user.email


class AdminUserListSerializer(serializers.Serializer):
    def to_representation(self, user):
        profile = get_or_create_customer_profile(user)
        return {
            'id': str(user.id),
            'name': _admin_user_name(user),
            'email': user.email,
            'imageUrl': '',
            'status': _admin_user_status(user),
            'role': _admin_user_role(user),
            'joined': user.date_joined,
            'company': profile.company or '',
            'phone': profile.phone or '',
        }


class AdminUserDetailSerializer(serializers.Serializer):
    def to_representation(self, user):
        profile = get_or_create_customer_profile(user)
        supplier_profile = getattr(user, 'supplier_profile', None)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': _admin_user_name(user),
            'status': _admin_user_status(user),
            'role': _admin_user_role(user),
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'phone': profile.phone or '',
            'company': profile.company or '',
            'country_code': profile.country_code or '',
            'preferred_currency': profile.preferred_currency or '',
            'receive_order_updates': profile.receive_order_updates,
            'receive_marketing_emails': profile.receive_marketing_emails,
            'supplier': {
                'is_supplier': supplier_profile is not None,
                'status': supplier_profile.status if supplier_profile else '',
                'company_name': supplier_profile.company_name if supplier_profile else '',
            },
        }


class AdminUserWriteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    company = serializers.CharField(required=False, allow_blank=True, max_length=120)
    role = serializers.ChoiceField(choices=ADMIN_USER_ROLE_CHOICES, required=False)
    status = serializers.ChoiceField(choices=[('active', 'Active'), ('suspended', 'Suspended')], required=False)
    password = serializers.CharField(required=False, allow_blank=False, trim_whitespace=False, write_only=True)

    def validate_email(self, value):
        email = value.strip().lower()
        instance = getattr(self, 'instance', None)
        queryset = User.objects.filter(email__iexact=email)
        if instance is not None:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Another account already uses this email.')
        return email

    def validate(self, attrs):
        password = attrs.get('password')
        if self.instance is None and not password:
            raise serializers.ValidationError({'password': 'Password is required when creating a user.'})
        if password:
            password_validation.validate_password(password, user=self.instance)

        role = attrs.get('role')
        if role == 'customer' and getattr(self.instance, 'supplier_profile', None):
            raise serializers.ValidationError({'role': 'Supplier accounts cannot be converted here.'})
        if role == 'staff' and getattr(self.instance, 'supplier_profile', None):
            raise serializers.ValidationError({'role': 'Supplier accounts cannot be converted here.'})
        if role == 'admin' and getattr(self.instance, 'supplier_profile', None):
            raise serializers.ValidationError({'role': 'Supplier accounts cannot be converted here.'})
        return attrs

    def _apply_role(self, user, role: str | None):
        if not role:
            return []
        dirty_fields = []
        desired_staff = role in {'staff', 'admin'}
        desired_superuser = role == 'admin'
        if user.is_staff != desired_staff:
            user.is_staff = desired_staff
            dirty_fields.append('is_staff')
        if user.is_superuser != desired_superuser:
            user.is_superuser = desired_superuser
            dirty_fields.append('is_superuser')
        return dirty_fields

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data.pop('password')
        role = validated_data.pop('role', 'customer')
        status_value = validated_data.pop('status', 'active')
        phone = validated_data.pop('phone', '').strip()
        company = validated_data.pop('company', '').strip()

        user = User.objects.create_user(
            username=self._generate_username(email),
            email=email,
            password=password,
            first_name=(validated_data.get('first_name', '') or '').strip(),
            last_name=(validated_data.get('last_name', '') or '').strip(),
        )
        user.is_active = status_value == 'active'
        dirty_fields = ['is_active']
        dirty_fields.extend(self._apply_role(user, role))
        if dirty_fields:
            user.save(update_fields=dirty_fields)

        profile = get_or_create_customer_profile(user)
        profile.phone = phone
        profile.company = company
        profile.save(update_fields=['phone', 'company'])
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)
        status_value = validated_data.pop('status', None)
        phone = validated_data.pop('phone', None)
        company = validated_data.pop('company', None)
        password = validated_data.pop('password', None)

        dirty_fields = []
        for field in ('email', 'first_name', 'last_name'):
            if field in validated_data:
                value = (validated_data[field] or '').strip() if isinstance(validated_data[field], str) else validated_data[field]
                if getattr(instance, field) != value:
                    setattr(instance, field, value)
                    dirty_fields.append(field)

        if status_value:
            desired_active = status_value == 'active'
            if instance.is_active != desired_active:
                instance.is_active = desired_active
                dirty_fields.append('is_active')

        dirty_fields.extend(self._apply_role(instance, role))

        if password:
            instance.set_password(password)
            dirty_fields.append('password')

        if dirty_fields:
            instance.save(update_fields=list(dict.fromkeys(dirty_fields)))

        profile = get_or_create_customer_profile(instance)
        profile_dirty_fields = []
        if phone is not None:
            phone = phone.strip()
            if profile.phone != phone:
                profile.phone = phone
                profile_dirty_fields.append('phone')
        if company is not None:
            company = company.strip()
            if profile.company != company:
                profile.company = company
                profile_dirty_fields.append('company')
        if profile_dirty_fields:
            profile.save(update_fields=profile_dirty_fields)

        return instance

    def _generate_username(self, email: str) -> str:
        base = email.split('@', 1)[0].strip().replace(' ', '_')[:120] or 'user'
        candidate = base
        suffix = 1
        while User.objects.filter(username__iexact=candidate).exists():
            suffix += 1
            candidate = f'{base[:140]}_{suffix}'
        return candidate[:150]
