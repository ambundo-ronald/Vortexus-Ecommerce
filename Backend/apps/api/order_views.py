from django.apps import apps
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from oscar.core.loading import get_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.inventory.services import InventoryReservationError, sync_basket_line_reservation
from apps.notifications.services import queue_shipping_update_email

from .order_serializers import (
    AdminOrderStatusUpdateSerializer,
    AdminOrderDetailSerializer,
    AdminOrderListSerializer,
    OrderListSerializer,
    OrderStatusSerializer,
    OrderSummarySerializer,
)


def _customer_orders_queryset(user):
    Order = get_model('order', 'Order')
    return (
        Order.objects.filter(user=user)
        .select_related('shipping_address', 'billing_address')
        .prefetch_related('lines__partner', 'lines__product', 'status_changes', 'supplier_groups__partner')
        .annotate(line_count=Count('lines', distinct=True), item_count=Sum('lines__quantity'))
        .order_by('-date_placed', '-id')
    )


def _admin_orders_queryset():
    Order = get_model('order', 'Order')
    return (
        Order.objects.select_related('user', 'user__customer_profile', 'shipping_address', 'billing_address')
        .prefetch_related('lines__partner', 'lines__product', 'status_changes', 'supplier_groups__partner', 'sources')
        .annotate(line_count=Count('lines', distinct=True), item_count=Sum('lines__quantity'))
        .order_by('-date_placed', '-id')
    )


def _cascade_admin_order_status(order, new_status: str, tracking_reference: str = '', note: str = ''):
    OrderStatusChange = apps.get_model('order', 'OrderStatusChange')
    ShippingEventType = apps.get_model('order', 'ShippingEventType')
    ShippingEvent = apps.get_model('order', 'ShippingEvent')
    ShippingEventQuantity = apps.get_model('order', 'ShippingEventQuantity')
    SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')

    line_status_map = {
        'Pending': 'pending',
        'Processing': 'processing',
        'Packed': 'packed',
        'Shipped': 'shipped',
        'Delivered': 'delivered',
        'Cancelled': 'cancelled',
    }
    group_status_map = {
        'Pending': 'pending',
        'Processing': 'processing',
        'Packed': 'packed',
        'Shipped': 'shipped',
        'Delivered': 'delivered',
        'Cancelled': 'cancelled',
    }

    line_status = line_status_map.get(new_status)
    group_status = group_status_map.get(new_status)

    changed_lines = []
    for line in order.lines.select_related('partner').all():
        old_line_status = (line.status or '').strip().lower()
        if line_status:
            if old_line_status != line_status:
                line.status = line_status
                line.save(update_fields=['status'])
                changed_lines.append(line)

            if old_line_status not in {'shipped', 'delivered'} and line_status in {'shipped', 'delivered'}:
                if getattr(line, 'num_allocated', 0):
                    line.consume_allocation(line.num_allocated)
            elif old_line_status not in {'cancelled', 'shipped', 'delivered'} and line_status == 'cancelled':
                if getattr(line, 'num_allocated', 0):
                    line.cancel_allocation(line.num_allocated)

    if group_status:
        update_fields = ['status', 'updated_at']
        group_updates = {'status': group_status}
        if tracking_reference:
            group_updates['tracking_reference'] = tracking_reference
            update_fields.append('tracking_reference')
        if note:
            group_updates['notes'] = note
            update_fields.append('notes')

        SupplierOrderGroup.objects.filter(order=order).update(**group_updates)

    if new_status in {'Processing', 'Packed', 'Shipped', 'Delivered', 'Cancelled'} or note or tracking_reference:
        event_type, _ = ShippingEventType.objects.get_or_create(
            code=(new_status or 'pending').lower(),
            defaults={'name': (new_status or 'Pending').replace('_', ' ').title()},
        )
        notes = f'Admin updated order {order.number} to {new_status}.'
        if tracking_reference:
            notes += f' Tracking: {tracking_reference}.'
        if note:
            notes += f' Note: {note}'
        event = ShippingEvent.objects.create(order=order, event_type=event_type, notes=notes)
        for line in changed_lines:
            ShippingEventQuantity.objects.create(event=event, line=line, quantity=line.quantity)

    previous_order_status = order.status or ''
    if previous_order_status != new_status:
        OrderStatusChange.objects.create(order=order, old_status=previous_order_status, new_status=new_status)
        order.status = new_status
        order.save(update_fields=['status'])

    return previous_order_status


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
        record_audit_event(
            event_type='orders.reordered',
            request=request,
            actor=request.user,
            target=order,
            message='Customer reordered items from a previous order.',
            metadata={'order_number': order.number, 'added_count': len(added), 'skipped_count': len(skipped)},
        )

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


class AdminOrderCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _admin_orders_queryset()
        query = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()

        if query:
            queryset = queryset.filter(
                Q(number__icontains=query)
                | Q(guest_email__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__customer_profile__company__icontains=query)
                | Q(shipping_address__line3__icontains=query)
                | Q(shipping_address__line4__icontains=query)
            )

        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        sort_by = (request.query_params.get('sort_by') or '').strip()
        if sort_by in {'price_desc', 'total_desc'}:
            queryset = queryset.order_by('-total_incl_tax', '-date_placed')
        elif sort_by in {'price_asc', 'total_asc'}:
            queryset = queryset.order_by('total_incl_tax', '-date_placed')
        elif sort_by == 'status':
            queryset = queryset.order_by('status', '-date_placed')
        else:
            queryset = queryset.order_by('-date_placed', '-id')

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
        serializer = AdminOrderListSerializer(page_obj.object_list, many=True)

        summary_queryset = _admin_orders_queryset()
        if query:
            summary_queryset = summary_queryset.filter(
                Q(number__icontains=query)
                | Q(guest_email__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__customer_profile__company__icontains=query)
                | Q(shipping_address__line3__icontains=query)
                | Q(shipping_address__line4__icontains=query)
            )

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
                'summary': {
                    'total': summary_queryset.count(),
                    'pending': summary_queryset.filter(status__in=['Pending', 'Processing', 'Packed']).count(),
                    'completed': summary_queryset.filter(status__in=['Paid', 'Shipped', 'Delivered', 'Complete', 'Completed']).count(),
                    'failed': summary_queryset.filter(status__in=['Failed', 'Cancelled', 'Canceled']).count(),
                },
            }
        )


class AdminOrderDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, order_id: int):
        order = get_object_or_404(_admin_orders_queryset(), id=order_id)
        return Response({'order': AdminOrderDetailSerializer(order).data})


class AdminOrderStatusAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def patch(self, request, order_id: int):
        order = get_object_or_404(_admin_orders_queryset(), id=order_id)
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')
        tracking_reference = serializer.validated_data.get('tracking_reference', '')

        previous_order_status = _cascade_admin_order_status(
            order,
            new_status=new_status,
            tracking_reference=tracking_reference,
            note=note,
        )
        order.refresh_from_db()

        if new_status in {'Shipped', 'Delivered'}:
            queue_shipping_update_email(
                order,
                status_label=new_status,
                tracking_reference=tracking_reference,
                note=note or 'Updated by admin.',
            )

        record_audit_event(
            event_type='orders.status_changed',
            request=request,
            actor=request.user,
            target=order,
            message='Admin updated order status.',
            metadata={
                'order_number': order.number,
                'previous_status': previous_order_status,
                'current_status': new_status,
                'tracking_reference': tracking_reference,
            },
        )

        return Response(
            {
                'detail': 'Order updated successfully.',
                'order': AdminOrderDetailSerializer(get_object_or_404(_admin_orders_queryset(), id=order.id)).data,
            }
        )
