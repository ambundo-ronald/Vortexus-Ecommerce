from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .checkout_serializers import (
    BasketItemCreateSerializer,
    BasketLineUpdateSerializer,
    ShippingAddressSerializer,
    ShippingMethodSelectionSerializer,
)
from .checkout_utils import (
    build_checkout_payload,
    clear_selected_shipping_method,
    get_checkout_session,
    get_shipping_address,
    get_shipping_methods,
)


class BasketAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'basket': build_checkout_payload(request)['basket']})


class BasketItemCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = BasketItemCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.basket.add_product(serializer.validated_data['product'], quantity=serializer.validated_data['quantity'])
        request.basket._lines = None
        return Response(build_checkout_payload(request), status=status.HTTP_201_CREATED)


class BasketLineDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, line_id: int):
        line = get_object_or_404(request.basket.lines.select_related('product', 'stockrecord'), id=line_id)
        serializer = BasketLineUpdateSerializer(data=request.data, context={'request': request, 'line': line})
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['quantity']
        if quantity == 0:
            line.delete()
        else:
            line.quantity = quantity
            line.save()

        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request))

    def delete(self, request, line_id: int):
        line = get_object_or_404(request.basket.lines.all(), id=line_id)
        line.delete()
        request.basket.reset_offer_applications()
        return Response(build_checkout_payload(request), status=status.HTTP_200_OK)


class ShippingStateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(build_checkout_payload(request))


class ShippingAddressAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request):
        serializer = ShippingAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        checkout_session = get_checkout_session(request)
        checkout_session.ship_to_new_address(serializer.to_session_fields())
        clear_selected_shipping_method(request)
        return Response(build_checkout_payload(request))


class ShippingMethodSelectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ShippingMethodSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_address = get_shipping_address(request, request.basket)
        methods = get_shipping_methods(request, request.basket, shipping_address=shipping_address)

        method_code = serializer.validated_data['method_code']
        method_codes = {method.code for method in methods}
        if method_code not in method_codes:
            return Response(
                {
                    'error': {
                        'code': 'invalid_shipping_method',
                        'detail': 'The selected shipping method is not available for this basket.',
                        'status': 400,
                        'errors': {'method_code': ['The selected shipping method is not available.']},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        get_checkout_session(request).use_shipping_method(method_code)
        return Response(build_checkout_payload(request))
