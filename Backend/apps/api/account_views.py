from django.contrib.auth import login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .account_serializers import (
    AccountLoginSerializer,
    AccountPasswordChangeSerializer,
    AccountProfileUpdateSerializer,
    AccountRegistrationSerializer,
    AccountSummarySerializer,
)


class CsrfTokenAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'csrf_token': get_token(request)})


class AccountRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return Response(
            {
                'user': AccountSummarySerializer(user).data,
                'csrf_token': get_token(request),
            },
            status=status.HTTP_201_CREATED,
        )


class AccountLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AccountLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(
            {
                'user': AccountSummarySerializer(user).data,
                'csrf_token': get_token(request),
            }
        )


class AccountLogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
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
        serializer = AccountProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'user': AccountSummarySerializer(user).data})


class AccountPasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AccountPasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        return Response({'detail': 'Password updated successfully.'})
