from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from oscar.core.loading import get_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.services import InventoryReservationError, sync_basket_line_reservation

from .order_serializers import OrderListSerializer, OrderStatusSerializer, OrderSummarySerializer


def _customer_orders_queryset(user):
    Order = get_model('order', 'Order')
    return (
        Order.objects.filter(user=user)
        .select_related('shipping_address', 'billing_address')
        .prefetch_related('lines__partner', 'lines__product', 'status_changes', 'supplier_groups__partner')
        .annotate(line_count=Count('lines', distinct=True), item_count=Sum('lines__quantity'))
        .order_by('-date_placed', '-id')
    )


class CustomerOrderCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = _customer_orders_queryset(request.user)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': {
                        'code': 'invalid_pagination',
                        'detail': 'Page and page_size must be integers.',
                        'status': 400,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = OrderListSerializer(page_obj.object_list, many=True)
        return Response(
            {
                'results': serializer.data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class CustomerOrderDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number: str):
        order = get_object_or_404(_customer_orders_queryset(request.user), number=order_number)
        return Response({'order': OrderSummarySerializer(order).data})


class CustomerOrderStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number: str):
        order = get_object_or_404(_customer_orders_queryset(request.user), number=order_number)
        return Response({'order': OrderStatusSerializer(order).data})


class CustomerOrderReorderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_number: str):
        order = get_object_or_404(_customer_orders_queryset(request.user), number=order_number)

        added = []
        skipped = []
        for line in order.lines.select_related('product').all():
            product = line.product
            if not product or not getattr(product, 'is_public', False):
                skipped.append({'line_id': line.id, 'reason': 'product_unavailable'})
                continue
            try:
                with transaction.atomic():
                    basket_line, _ = request.basket.add_product(product, quantity=line.quantity)
                    sync_basket_line_reservation(basket_line)
                added.append({'line_id': line.id, 'product_id': product.id, 'quantity': line.quantity})
            except InventoryReservationError:
                skipped.append({'line_id': line.id, 'reason': 'insufficient_stock'})

        request.basket._lines = None
        request.basket.reset_offer_applications()

        return Response(
            {
                'detail': 'Order items added to basket.',
                'order_number': order.number,
                'added': added,
                'skipped': skipped,
                'basket': {
                    'id': request.basket.id,
                    'item_count': request.basket.num_items,
                },
            },
            status=status.HTTP_200_OK,
        )
