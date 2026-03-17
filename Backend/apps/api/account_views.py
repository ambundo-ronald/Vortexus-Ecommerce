from django.contrib.auth import login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.notifications.services import queue_account_registration_email, queue_password_changed_email

from .throttles import AccountLoginIdentityThrottle, AccountRegisterIdentityThrottle
from .account_serializers import (
    AccountLoginSerializer,
    AccountPasswordChangeSerializer,
    AccountProfileUpdateSerializer,
    AccountRegistrationSerializer,
    AccountSummarySerializer,
)


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
        queue_account_registration_email(user)
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
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
        record_audit_event(
            event_type='account.profile_updated',
            request=request,
            actor=user,
            target=user,
            message='Account profile updated.',
            metadata={'previous_email': previous_email, 'current_email': user.email},
        )
        return Response({'user': AccountSummarySerializer(user).data})


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
