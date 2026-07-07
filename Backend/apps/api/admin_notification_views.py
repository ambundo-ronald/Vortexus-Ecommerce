from django.apps import apps
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.services import admin_notification_payload, web_push_is_configured


class PushSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.URLField()
    keys = serializers.DictField()
    browser = serializers.CharField(required=False, allow_blank=True, max_length=120)

    def validate_keys(self, value):
        if not value.get('p256dh') or not value.get('auth'):
            raise serializers.ValidationError('Subscription keys must include p256dh and auth.')
        return value


class AdminNotificationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        AdminNotification = apps.get_model('notifications', 'AdminNotification')
        queryset = AdminNotification.objects.filter(user=request.user)
        unread_only = str(request.query_params.get('unread') or '').lower() in {'1', 'true', 'yes'}
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)

        try:
            limit = min(max(int(request.query_params.get('limit', 25) or 25), 1), 100)
        except (TypeError, ValueError):
            limit = 25

        unread_count = AdminNotification.objects.filter(user=request.user, read_at__isnull=True).count()
        results = [admin_notification_payload(item) for item in queryset[:limit]]
        return Response({'results': results, 'unread_count': unread_count})


class AdminNotificationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, notification_id: int):
        AdminNotification = apps.get_model('notifications', 'AdminNotification')
        notification = AdminNotification.objects.filter(user=request.user, id=notification_id).first()
        if not notification:
            return Response(
                {'error': {'code': 'notification_not_found', 'detail': 'Notification not found.', 'status': 404}},
                status=status.HTTP_404_NOT_FOUND,
            )
        action = (request.data.get('action') or 'read').strip().lower()
        if action == 'unread':
            notification.read_at = None
        else:
            notification.read_at = timezone.now()
        notification.save(update_fields=['read_at', 'updated_at'])
        return Response({'notification': admin_notification_payload(notification)})


class AdminNotificationReadAllAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        AdminNotification = apps.get_model('notifications', 'AdminNotification')
        updated = AdminNotification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response({'updated': updated})


class AdminPushConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.conf import settings

        PushSubscription = apps.get_model('notifications', 'PushSubscription')
        active_subscription_count = PushSubscription.objects.filter(
            user=request.user,
            channel=PushSubscription.CHANNEL_ADMIN,
            is_enabled=True,
        ).count()
        return Response(
            {
                'is_configured': web_push_is_configured(),
                'public_key': settings.WEB_PUSH_VAPID_PUBLIC_KEY,
                'active_subscription_count': active_subscription_count,
            }
        )


class AdminPushSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data.get('subscription') or request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        keys = data['keys']
        PushSubscription = apps.get_model('notifications', 'PushSubscription')
        subscription, _ = PushSubscription.objects.update_or_create(
            endpoint=data['endpoint'],
            defaults={
                'user': request.user,
                'channel': PushSubscription.CHANNEL_ADMIN,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
                'browser': data.get('browser', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'is_enabled': True,
                'last_seen_at': timezone.now(),
            },
        )
        return Response({'id': subscription.id, 'is_enabled': subscription.is_enabled}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        endpoint = (request.data.get('endpoint') or '').strip()
        if not endpoint:
            raise serializers.ValidationError({'endpoint': 'Endpoint is required.'})
        PushSubscription = apps.get_model('notifications', 'PushSubscription')
        updated = PushSubscription.objects.filter(
            user=request.user,
            channel=PushSubscription.CHANNEL_ADMIN,
            endpoint=endpoint,
        ).update(is_enabled=False, updated_at=timezone.now())
        return Response({'updated': updated})
