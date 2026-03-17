from django.apps import apps
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.payments.mpesa import (
    MpesaConfigurationError,
    MpesaGatewayError,
    find_payment_by_callback_reference,
    handle_callback,
    initiate_stk_push,
    mpesa_is_configured,
    query_stk_push_status,
)
from apps.payments.card import CardGatewayError, authorize_card_payment
from apps.payments.airtel_money import (
    AirtelMoneyGatewayError,
    airtel_money_is_configured,
    find_payment_by_airtel_reference,
    handle_airtel_callback,
    initiate_airtel_collection,
)
from apps.payments.services import (
    available_payment_methods,
    confirm_payment_session,
    initialize_payment_session,
    serialize_payment_session,
)

from .payment_serializers import (
    AirtelMoneyCallbackSerializer,
    AirtelMoneyInitializationSerializer,
    CardInitializationSerializer,
    MpesaCallbackSerializer,
    MpesaInitializationSerializer,
    PaymentConfirmationSerializer,
    PaymentInitializationSerializer,
    PaymentMethodSerializer,
)


class PaymentMethodCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = PaymentMethodSerializer(available_payment_methods(), many=True)
        return Response({'results': serializer.data})


class PaymentInitializationAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'payment_init'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = PaymentInitializationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        pricing = serializer.validated_data['pricing']
        payment_session = initialize_payment_session(
            basket=request.basket,
            user=request.user,
            method_code=serializer.validated_data['method'],
            amount=pricing['order_total'].incl_tax,
            currency=pricing['order_total'].currency,
            payer_email=serializer.validated_data['payer_email'],
            payer_phone=serializer.validated_data['phone_number'],
            metadata={
                'basket_id': request.basket.id,
                'shipping_method': serializer.validated_data['shipping_method'].code if serializer.validated_data['shipping_method'] else '',
                'country_code': pricing['tax_breakdown']['country_code'],
            },
        )
        return Response({'payment': serialize_payment_session(payment_session)}, status=status.HTTP_201_CREATED)


class PaymentSessionDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, reference: str):
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = get_object_or_404(PaymentSession, reference=reference)
        return Response({'payment': serialize_payment_session(payment_session)})


class PaymentConfirmationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, reference: str):
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = get_object_or_404(PaymentSession, reference=reference)
        serializer = PaymentConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_session = confirm_payment_session(
            payment_session,
            success=serializer.validated_data['success'],
            external_reference=serializer.validated_data.get('external_reference', ''),
            metadata={'confirmed_via': 'api'},
        )
        return Response({'payment': serialize_payment_session(payment_session)})


class MpesaInitializationAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'payment_init'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        if not mpesa_is_configured():
            return Response(
                {
                    'error': {
                        'code': 'mpesa_not_configured',
                        'detail': 'M-Pesa sandbox credentials are not configured on the backend.',
                        'status': 503,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = MpesaInitializationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        pricing = serializer.validated_data['pricing']
        payment_session = initialize_payment_session(
            basket=request.basket,
            user=request.user,
            method_code='mpesa',
            amount=pricing['order_total'].incl_tax,
            currency=pricing['order_total'].currency,
            payer_email=serializer.validated_data['payer_email'],
            payer_phone=serializer.validated_data['phone_number'],
            metadata={
                'basket_id': request.basket.id,
                'shipping_method': serializer.validated_data['shipping_method'].code if serializer.validated_data['shipping_method'] else '',
                'country_code': pricing['tax_breakdown']['country_code'],
                'integration': 'daraja_sandbox',
            },
        )
        try:
            provider_payload = initiate_stk_push(payment_session)
        except (MpesaConfigurationError, MpesaGatewayError) as exc:
            payment_session.status = payment_session.STATUS_FAILED
            payment_session.metadata = {**payment_session.metadata, 'gateway_error': str(exc)}
            payment_session.save(update_fields=['status', 'metadata', 'updated_at'])
            return Response(
                {
                    'error': {
                        'code': 'mpesa_gateway_error',
                        'detail': str(exc),
                        'status': 502,
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = serialize_payment_session(payment_session)
        payload['provider_payload'] = provider_payload
        return Response({'payment': payload}, status=status.HTTP_201_CREATED)


class MpesaStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, reference: str):
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = get_object_or_404(PaymentSession, reference=reference, method='mpesa')
        if mpesa_is_configured():
            try:
                query_data = query_stk_push_status(payment_session)
                payment_session.metadata = {**payment_session.metadata, 'last_query': query_data}
                payment_session.save(update_fields=['metadata', 'updated_at'])
            except (MpesaConfigurationError, MpesaGatewayError):
                pass
        return Response({'payment': serialize_payment_session(payment_session)})


class MpesaCallbackAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = MpesaCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = find_payment_by_callback_reference(PaymentSession, serializer.validated_data)
        if payment_session is None:
            return Response(
                {
                    'error': {
                        'code': 'mpesa_payment_not_found',
                        'detail': 'No payment session matched the callback identifiers.',
                        'status': 404,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        payment_session = handle_callback(payment_session, serializer.validated_data)
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted', 'payment': serialize_payment_session(payment_session)})


class CardInitializationAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'payment_init'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = CardInitializationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        pricing = serializer.validated_data['pricing']
        payment_session = initialize_payment_session(
            basket=request.basket,
            user=request.user,
            method_code=serializer.validated_data['method'],
            amount=pricing['order_total'].incl_tax,
            currency=pricing['order_total'].currency,
            payer_email=serializer.validated_data['payer_email'],
            metadata={
                'basket_id': request.basket.id,
                'shipping_method': serializer.validated_data['shipping_method'].code if serializer.validated_data['shipping_method'] else '',
                'country_code': pricing['tax_breakdown']['country_code'],
                'integration': 'card_sandbox',
            },
        )
        try:
            payment_session = authorize_card_payment(
                payment_session,
                payment_token=serializer.validated_data['payment_token'],
                card_brand=serializer.validated_data.get('card_brand', ''),
                last4=serializer.validated_data.get('last4', ''),
                expiry_month=serializer.validated_data.get('expiry_month'),
                expiry_year=serializer.validated_data.get('expiry_year'),
                holder_name=serializer.validated_data.get('holder_name', ''),
            )
        except CardGatewayError as exc:
            payment_session.status = payment_session.STATUS_FAILED
            payment_session.metadata = {**payment_session.metadata, 'gateway_error': str(exc)}
            payment_session.save(update_fields=['status', 'metadata', 'updated_at'])
            return Response(
                {
                    'error': {
                        'code': 'card_gateway_error',
                        'detail': str(exc),
                        'status': 502,
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'payment': serialize_payment_session(payment_session)}, status=status.HTTP_201_CREATED)


class AirtelMoneyInitializationAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'payment_init'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        if not airtel_money_is_configured():
            return Response(
                {
                    'error': {
                        'code': 'airtel_money_not_configured',
                        'detail': 'Airtel Money sandbox is not configured on the backend.',
                        'status': 503,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = AirtelMoneyInitializationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        pricing = serializer.validated_data['pricing']
        payment_session = initialize_payment_session(
            basket=request.basket,
            user=request.user,
            method_code='airtel_money',
            amount=pricing['order_total'].incl_tax,
            currency=pricing['order_total'].currency,
            payer_email=serializer.validated_data['payer_email'],
            payer_phone=serializer.validated_data['phone_number'],
            metadata={
                'basket_id': request.basket.id,
                'shipping_method': serializer.validated_data['shipping_method'].code if serializer.validated_data['shipping_method'] else '',
                'country_code': pricing['tax_breakdown']['country_code'],
                'integration': 'airtel_money_sandbox',
            },
        )
        try:
            provider_payload = initiate_airtel_collection(payment_session)
        except AirtelMoneyGatewayError as exc:
            payment_session.status = payment_session.STATUS_FAILED
            payment_session.metadata = {**payment_session.metadata, 'gateway_error': str(exc)}
            payment_session.save(update_fields=['status', 'metadata', 'updated_at'])
            return Response(
                {
                    'error': {
                        'code': 'airtel_money_gateway_error',
                        'detail': str(exc),
                        'status': 502,
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = serialize_payment_session(payment_session)
        payload['provider_payload'] = provider_payload
        return Response({'payment': payload}, status=status.HTTP_201_CREATED)


class AirtelMoneyStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, reference: str):
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = get_object_or_404(PaymentSession, reference=reference, method='airtel_money')
        return Response({'payment': serialize_payment_session(payment_session)})


class AirtelMoneyCallbackAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AirtelMoneyCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PaymentSession = apps.get_model('payments', 'PaymentSession')
        payment_session = find_payment_by_airtel_reference(PaymentSession, serializer.validated_data)
        if payment_session is None:
            return Response(
                {
                    'error': {
                        'code': 'airtel_money_payment_not_found',
                        'detail': 'No Airtel Money payment session matched the callback identifiers.',
                        'status': 404,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        payment_session = handle_airtel_callback(payment_session, serializer.validated_data)
        return Response({'status': 'accepted', 'payment': serialize_payment_session(payment_session)})
