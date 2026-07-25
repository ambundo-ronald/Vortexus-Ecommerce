from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from oscar.core.loading import get_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import CallbackRequest


WORKDAY_START = time(7, 0)
WORKDAY_END = time(20, 0)
CALLBACK_SLA = timedelta(hours=3)
CALLBACK_BUSINESS_TIMEZONE = ZoneInfo(getattr(settings, 'CALLBACK_BUSINESS_TIME_ZONE', 'Africa/Nairobi'))


def callback_respond_by(created_at):
    """Add three hours while consuming time only during weekday working hours."""
    current = timezone.localtime(created_at, CALLBACK_BUSINESS_TIMEZONE)
    remaining = CALLBACK_SLA

    while True:
        if current.weekday() >= 5:
            days_until_monday = 7 - current.weekday()
            next_date = current.date() + timedelta(days=days_until_monday)
            current = timezone.make_aware(datetime.combine(next_date, WORKDAY_START), current.tzinfo)
            continue

        day_start = timezone.make_aware(datetime.combine(current.date(), WORKDAY_START), current.tzinfo)
        day_end = timezone.make_aware(datetime.combine(current.date(), WORKDAY_END), current.tzinfo)
        if current < day_start:
            current = day_start
        elif current >= day_end:
            current = timezone.make_aware(
                datetime.combine(current.date() + timedelta(days=1), WORKDAY_START),
                current.tzinfo,
            )
            continue

        available = day_end - current
        if remaining <= available:
            return current + remaining
        remaining -= available
        current = timezone.make_aware(
            datetime.combine(current.date() + timedelta(days=1), WORKDAY_START),
            current.tzinfo,
        )


class CallbackRequestCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=160)
    phone_number = serializers.RegexField(
        regex=r'^\+?[0-9][0-9\s().-]{6,30}$',
        max_length=32,
        error_messages={'invalid': 'Enter a valid phone number.'},
    )
    reason = serializers.CharField(min_length=5, max_length=2000)

    def validate_product_id(self, value):
        Product = get_model('catalogue', 'Product')
        try:
            self.product = Product.objects.get(pk=value)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError('Product not found.') from exc
        return value

    def create(self, validated_data):
        request = self.context['request']
        now = timezone.now()
        return CallbackRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            product=self.product,
            name=validated_data['name'].strip(),
            phone_number=validated_data['phone_number'].strip(),
            reason=validated_data['reason'].strip(),
            respond_by=callback_respond_by(now),
        )


class CallbackRequestCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'callback_request'

    def post(self, request):
        serializer = CallbackRequestCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        callback_request = serializer.save()
        return Response(
            {
                'id': callback_request.id,
                'status': callback_request.status,
                'respond_by': callback_request.respond_by,
                'message': 'Your callback request has been received.',
            },
            status=status.HTTP_201_CREATED,
        )


class AdminCallbackRequestDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, callback_id):
        try:
            callback_request = CallbackRequest.objects.get(pk=callback_id)
        except CallbackRequest.DoesNotExist:
            return Response({'detail': 'Callback request not found.'}, status=status.HTTP_404_NOT_FOUND)

        requested_status = request.data.get('status', callback_request.status)
        valid_statuses = {choice[0] for choice in CallbackRequest.STATUS_CHOICES}
        if requested_status not in valid_statuses:
            return Response({'status': ['Invalid callback status.']}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        callback_request.status = requested_status
        callback_request.staff_notes = str(request.data.get('staff_notes', callback_request.staff_notes)).strip()
        callback_request.assigned_to = request.user
        if requested_status == CallbackRequest.STATUS_CONTACTED and not callback_request.contacted_at:
            callback_request.contacted_at = now
        if requested_status == CallbackRequest.STATUS_RESOLVED:
            callback_request.contacted_at = callback_request.contacted_at or now
            callback_request.resolved_at = now
        callback_request.save()
        return Response({'id': callback_request.id, 'status': callback_request.status})
