from django.apps import apps
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.tokens import email_verification_token_generator
from apps.accounts.two_factor import (
    TWO_FACTOR_CODE_TTL_MINUTES,
    TWO_FACTOR_MAX_ATTEMPTS,
    create_email_two_factor_challenge,
    generate_two_factor_code,
    verify_email_two_factor_challenge,
)
from apps.auditlog.services import record_audit_event
from apps.common.async_utils import dispatch_background_task
from apps.integrations.tasks import sync_customer_to_erpnext
from apps.notifications.services import (
    queue_account_reactivation_request_email,
    queue_email_two_factor_code,
    queue_email_verification_email,
    queue_password_changed_email,
)

from .throttles import AccountLoginIdentityThrottle, AccountRegisterIdentityThrottle
from .account_serializers import (
    AccountLoginSerializer,
    AccountPasswordChangeSerializer,
    AccountProfileUpdateSerializer,
    AccountReactivationRequestSerializer,
    AccountRegistrationSerializer,
    AccountSummarySerializer,
    get_or_create_customer_profile,
)


def _mask_email(email: str) -> str:
    local_part, separator, domain = (email or '').partition('@')
    if not separator:
        return email or ''
    if len(local_part) <= 2:
        masked_local = f'{local_part[:1]}***'
    else:
        masked_local = f'{local_part[:2]}***{local_part[-1:]}'
    return f'{masked_local}@{domain}'


class CsrfTokenAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_csrf'

    def get(self, request):
        return Response({'csrf_token': get_token(request)})


class AccountRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_register'
    throttle_classes = [ScopedRateThrottle, AccountRegisterIdentityThrottle]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, APIException):
            record_audit_event(
                event_type='account.registration_failed',
                request=request,
                status='failure',
                message='Account registration failed.',
                metadata={'email': request.data.get('email', '')},
            )
            raise
        user = serializer.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        queue_email_verification_email(user)
        dispatch_background_task(
            sync_customer_to_erpnext,
            run_kwargs={'user_id': user.id},
            async_kwargs={'user_id': user.id},
        )
        record_audit_event(
            event_type='account.registered',
            request=request,
            actor=user,
            target=user,
            message='Customer account registered.',
        )
        return Response(
            {
                'user': AccountSummarySerializer(user).data,
                'csrf_token': get_token(request),
            },
            status=status.HTTP_201_CREATED,
        )


class AccountLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_login'
    throttle_classes = [ScopedRateThrottle, AccountLoginIdentityThrottle]

    def post(self, request):
        serializer = AccountLoginSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, APIException):
            record_audit_event(
                event_type='account.login_failed',
                request=request,
                status='failure',
                message='Account login failed.',
                metadata={'identifier': request.data.get('identifier', ''), 'email': request.data.get('email', '')},
            )
            raise
        user = serializer.validated_data['user']
        profile = get_or_create_customer_profile(user)
        if profile.two_factor_email_enabled:
            code = generate_two_factor_code()
            challenge = create_email_two_factor_challenge(user, code)
            queue_email_two_factor_code(user, code=code)
            record_audit_event(
                event_type='account.login_two_factor_required',
                request=request,
                actor=user,
                target=user,
                message='Account login requires email 2FA.',
                metadata={'email': user.email},
            )
            return Response(
                {
                    'requires_2fa': True,
                    'challenge_id': challenge.id,
                    'detail': 'Enter the verification code sent to your email.',
                    'email_mask': _mask_email(user.email),
                    'expires_at': challenge.expires_at.isoformat(),
                    'expires_in_seconds': int(TWO_FACTOR_CODE_TTL_MINUTES * 60),
                    'max_attempts': TWO_FACTOR_MAX_ATTEMPTS,
                }
            )
        login(request, user)
        record_audit_event(
            event_type='account.logged_in',
            request=request,
            actor=user,
            target=user,
            message='Account login successful.',
        )
        return Response(
            {
                'user': AccountSummarySerializer(user).data,
                'csrf_token': get_token(request),
            }
        )


class AccountLoginTwoFactorAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_login_2fa'

    def post(self, request):
        challenge_id = request.data.get('challenge_id')
        code = str(request.data.get('code', '')).strip()
        Challenge = apps.get_model('accounts', 'EmailTwoFactorChallenge')
        challenge = get_object_or_404(Challenge.objects.select_related('user'), id=challenge_id)
        ok, error = verify_email_two_factor_challenge(challenge, code)
        if not ok:
            record_audit_event(
                event_type='account.login_two_factor_failed',
                request=request,
                actor=challenge.user,
                target=challenge.user,
                status='failure',
                message='Email 2FA login failed.',
                metadata={'email': challenge.user.email},
            )
            remaining_attempts = max(TWO_FACTOR_MAX_ATTEMPTS - challenge.attempts, 0)
            raise ValidationError({'detail': error, 'remaining_attempts': remaining_attempts})

        user = challenge.user
        if not user.is_active:
            raise ValidationError({'detail': 'This account is inactive.'})
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        record_audit_event(
            event_type='account.logged_in',
            request=request,
            actor=user,
            target=user,
            message='Account login successful with email 2FA.',
        )
        return Response(
            {
                'user': AccountSummarySerializer(user).data,
                'csrf_token': get_token(request),
            }
        )


class AccountReactivationRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_reactivation_request'

    def post(self, request):
        serializer = AccountReactivationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        inactive_user = serializer.validated_data.get('inactive_user')
        if inactive_user:
            queue_account_reactivation_request_email(inactive_user, requested_by=identifier)
        record_audit_event(
            event_type='account.reactivation_requested',
            request=request,
            actor=inactive_user,
            target=inactive_user,
            message='Customer account reactivation requested.',
            metadata={'identifier': identifier, 'matched_inactive_account': bool(inactive_user)},
        )
        return Response(
            {
                'detail': (
                    'If this email belongs to a deactivated account, our support team will review the reactivation request.'
                )
            }
        )


class AccountLogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        logout(request)
        record_audit_event(
            event_type='account.logged_out',
            request=request,
            actor=user,
            target=user,
            message='Account logged out.',
        )
        return Response(
            {
                'detail': 'Logged out successfully.',
                'csrf_token': get_token(request),
            }
        )


class AccountProfileAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'user': None})
        return Response({'user': AccountSummarySerializer(request.user).data})

    def patch(self, request):
        previous_email = request.user.email
        serializer = AccountProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if previous_email != user.email:
            queue_email_verification_email(user)
        dispatch_background_task(
            sync_customer_to_erpnext,
            run_kwargs={'user_id': user.id},
            async_kwargs={'user_id': user.id},
        )
        record_audit_event(
            event_type='account.profile_updated',
            request=request,
            actor=user,
            target=user,
            message='Account profile updated.',
            metadata={'previous_email': previous_email, 'current_email': user.email},
        )
        return Response({'user': AccountSummarySerializer(user).data})


class AccountEmailVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'account_email_verify'

    def post(self, request):
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
        except Exception as exc:
            raise ValidationError({'uid': 'Invalid verification link.'}) from exc
        if not user_id:
            raise ValidationError({'uid': 'Invalid verification link.'})

        user = get_object_or_404(get_user_model(), pk=user_id)
        if not email_verification_token_generator.check_token(user, token):
            raise ValidationError({'token': 'Invalid, expired, or already-used verification token. Links expire in 30 minutes.'})

        profile = get_or_create_customer_profile(user)
        if profile.email_verified_at is None:
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=['email_verified_at', 'updated_at'])

        record_audit_event(
            event_type='account.email_verified',
            request=request,
            actor=user,
            target=user,
            message='Account email verified.',
            metadata={'email': user.email},
        )
        return Response({'detail': 'Email verified successfully.', 'user': AccountSummarySerializer(user).data})


class AccountEmailVerificationResendAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'account_email_verify_resend'

    def post(self, request):
        profile = get_or_create_customer_profile(request.user)
        if profile.email_verified_at is not None:
            return Response({'detail': 'Email is already verified.', 'user': AccountSummarySerializer(request.user).data})

        queue_email_verification_email(request.user)
        record_audit_event(
            event_type='account.email_verification_resent',
            request=request,
            actor=request.user,
            target=request.user,
            message='Account email verification resent.',
            metadata={'email': request.user.email},
        )
        return Response({'detail': 'Verification email sent.'})


class AccountPasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'account_password'

    def post(self, request):
        serializer = AccountPasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        queue_password_changed_email(user)
        record_audit_event(
            event_type='account.password_changed',
            request=request,
            actor=user,
            target=user,
            message='Account password changed.',
        )
        return Response({'detail': 'Password updated successfully.'})
