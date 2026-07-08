from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from oscar.core.loading import get_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.models import SearchAnalyticsEvent
from apps.common.products import stockrecord_count


def _decimal_to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _order_customer_name(order):
    user = getattr(order, 'user', None)
    if user:
        full_name = (user.get_full_name() or '').strip()
        if full_name:
            return full_name
        if user.email:
            return user.email
    return (getattr(order, 'guest_email', '') or '').strip() or 'Guest Customer'


def _product_image_url(product):
    if not product:
        return ''
    try:
        primary = product.primary_image()
    except TypeError:
        primary = product.primary_image
    except Exception:
        primary = None
    original = getattr(primary, 'original', None)
    return getattr(original, 'url', '') if original else ''


def _product_category_name(product):
    if not product:
        return 'Uncategorized'
    category = product.categories.order_by('depth', 'name').first()
    return category.name if category else 'Uncategorized'


def _available_stock_for_product(product):
    if not product:
        return 0
    return sum(stockrecord_count(stockrecord) for stockrecord in product.stockrecords.all())


class AdminDashboardAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        Line = get_model('order', 'Line')
        Product = get_model('catalogue', 'Product')
        StockRecord = get_model('partner', 'StockRecord')
        ProductImage = get_model('catalogue', 'ProductImage')
        User = get_user_model()

        now = timezone.now()
        days = min(max(int(request.query_params.get('days', 30) or 30), 1), 365)
        start = now - timedelta(days=days - 1)

        orders = Order.objects.all()
        recent_orders = orders.filter(date_placed__date__gte=start.date())
        products = Product.objects.all()
        users = User.objects.all()

        total_revenue = orders.aggregate(total=Sum('total_incl_tax'))['total'] or Decimal('0')
        recent_revenue = recent_orders.aggregate(total=Sum('total_incl_tax'))['total'] or Decimal('0')

        pending_statuses = ['Pending', 'Processing', 'Packed']
        completed_statuses = ['Paid', 'Shipped', 'Delivered', 'Complete', 'Completed']
        failed_statuses = ['Failed', 'Cancelled', 'Canceled']

        stock_summary = StockRecord.objects.aggregate(total=Sum('num_in_stock'))
        low_stock_products = (
            StockRecord.objects.values('product_id')
            .annotate(total_stock=Sum('num_in_stock'))
            .filter(total_stock__gt=0, total_stock__lt=10)
            .count()
        )
        out_of_stock_products = (
            StockRecord.objects.values('product_id')
            .annotate(total_stock=Sum('num_in_stock'))
            .filter(total_stock__lte=0)
            .count()
        )

        daily_rows = {
            row['day']: row
            for row in recent_orders.annotate(day=TruncDate('date_placed'))
            .values('day')
            .annotate(orders=Count('id'), revenue=Sum('total_incl_tax'))
            .order_by('day')
        }
        daily_series = []
        for offset in range(days):
            day = (start + timedelta(days=offset)).date()
            row = daily_rows.get(day, {})
            daily_series.append(
                {
                    'date': day.isoformat(),
                    'orders': row.get('orders', 0) or 0,
                    'revenue': _decimal_to_float(row.get('revenue')),
                }
            )

        latest_orders = [
            {
                'id': order.id,
                'number': order.number,
                'customer': _order_customer_name(order),
                'date': order.date_placed,
                'total': _decimal_to_float(order.total_incl_tax),
                'currency': order.currency or getattr(settings, 'OSCAR_DEFAULT_CURRENCY', 'KES'),
                'status': order.status or 'Pending',
            }
            for order in orders.select_related('user').order_by('-date_placed', '-id')[:8]
        ]

        popular_rows = (
            Line.objects.exclude(product_id=None)
            .values('product_id', 'product__title')
            .annotate(quantity=Sum('quantity'))
            .order_by('-quantity')[:8]
        )
        popular_product_ids = [row['product_id'] for row in popular_rows]
        product_map = {
            product.id: product
            for product in Product.objects.filter(id__in=popular_product_ids).prefetch_related('categories', 'images', 'stockrecords')
        }
        popular_products = []
        for row in popular_rows:
            product = product_map.get(row['product_id'])
            popular_products.append(
                {
                    'id': row['product_id'],
                    'name': row['product__title'] or getattr(product, 'title', ''),
                    'category': _product_category_name(product),
                    'stock': _available_stock_for_product(product),
                    'quantity_sold': row['quantity'] or 0,
                    'image': _product_image_url(product),
                }
            )

        if not popular_products:
            for product in products.prefetch_related('categories', 'images', 'stockrecords').order_by('-date_created', '-id')[:8]:
                stock = _available_stock_for_product(product)
                popular_products.append(
                    {
                        'id': product.id,
                        'name': product.title,
                        'category': _product_category_name(product),
                        'stock': stock,
                        'quantity_sold': 0,
                        'image': _product_image_url(product),
                    }
                )

        category_counts = {}
        for product in products.prefetch_related('categories')[:1000]:
            category = _product_category_name(product)
            category_counts[category] = category_counts.get(category, 0) + 1
        total_categorized = sum(category_counts.values()) or 1
        colors = ['#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2']
        category_share = [
            {
                'name': name,
                'value': round((count / total_categorized) * 100),
                'color': colors[index % len(colors)],
            }
            for index, (name, count) in enumerate(sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:6])
        ]

        return Response(
            {
                'range': {'days': days, 'start': start.date(), 'end': now.date()},
                'currency': getattr(settings, 'OSCAR_DEFAULT_CURRENCY', 'KES'),
                'kpis': {
                    'orders': orders.count(),
                    'recent_orders': recent_orders.count(),
                    'revenue': _decimal_to_float(total_revenue),
                    'recent_revenue': _decimal_to_float(recent_revenue),
                    'products': products.count(),
                    'active_products': products.filter(is_public=True).count(),
                    'users': users.count(),
                    'staff_users': users.filter(is_staff=True).count(),
                    'media_assets': ProductImage.objects.count(),
                    'stock_units': stock_summary['total'] or 0,
                    'low_stock_products': low_stock_products,
                    'out_of_stock_products': out_of_stock_products,
                },
                'order_status': {
                    'pending': orders.filter(status__in=pending_statuses).count(),
                    'completed': orders.filter(status__in=completed_statuses).count(),
                    'failed': orders.filter(status__in=failed_statuses).count(),
                },
                'daily': daily_series,
                'latest_orders': latest_orders,
                'popular_products': popular_products,
                'category_share': category_share,
            }
        )


class AdminSearchAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        days = min(max(int(request.query_params.get('days', 30) or 30), 1), 365)
        start = now - timedelta(days=days - 1)
        events = SearchAnalyticsEvent.objects.filter(created_at__date__gte=start.date())
        search_events = events.filter(
            event_type__in=[
                SearchAnalyticsEvent.EVENT_SEARCH_SUBMITTED,
                SearchAnalyticsEvent.EVENT_RESULTS_VIEWED,
                SearchAnalyticsEvent.EVENT_NO_RESULTS,
                SearchAnalyticsEvent.EVENT_IMAGE_SEARCH_SUBMITTED,
            ]
        )
        contexts = search_events.exclude(search_context_id='').values_list('search_context_id', flat=True).distinct()
        context_count = contexts.count()
        cart_contexts = (
            events.filter(event_type=SearchAnalyticsEvent.EVENT_CART_ADDED, search_context_id__in=contexts)
            .exclude(search_context_id='')
            .values_list('search_context_id', flat=True)
            .distinct()
            .count()
        )
        order_contexts = (
            events.filter(event_type=SearchAnalyticsEvent.EVENT_ORDER_CONVERTED, search_context_id__in=contexts)
            .exclude(search_context_id='')
            .values_list('search_context_id', flat=True)
            .distinct()
            .count()
        )

        top_terms = [
            {
                'query': row['query'],
                'count': row['count'],
                'avg_results': round(float(row['avg_results'] or 0), 1),
                'last_seen': row['last_seen'],
            }
            for row in events.exclude(query='')
            .filter(event_type__in=[SearchAnalyticsEvent.EVENT_SEARCH_SUBMITTED, SearchAnalyticsEvent.EVENT_RESULTS_VIEWED])
            .values('query')
            .annotate(count=Count('id'), avg_results=Avg('result_count'), last_seen=Max('created_at'))
            .order_by('-count', 'query')[:20]
        ]
        zero_result_terms = [
            {
                'query': row['query'] or '(empty)',
                'count': row['count'],
                'last_seen': row['last_seen'],
            }
            for row in events.filter(event_type=SearchAnalyticsEvent.EVENT_NO_RESULTS)
            .values('query')
            .annotate(count=Count('id'), last_seen=Max('created_at'))
            .order_by('-count', 'query')[:20]
        ]
        clicked_products = [
            {
                'product_id': row['product_id'],
                'product_title': row['product_title'] or f"Product #{row['product_id']}",
                'clicks': row['clicks'],
                'last_seen': row['last_seen'],
            }
            for row in events.filter(event_type=SearchAnalyticsEvent.EVENT_PRODUCT_CLICKED)
            .exclude(product_id=None)
            .values('product_id', 'product_title')
            .annotate(clicks=Count('id'), last_seen=Max('created_at'))
            .order_by('-clicks', 'product_title')[:20]
        ]
        user_searches = [
            {
                'user_email': row['user_email'] or 'Anonymous',
                'anonymous_id': row['anonymous_id'],
                'searches': row['searches'],
                'last_seen': row['last_seen'],
            }
            for row in search_events.values('user_email', 'anonymous_id')
            .annotate(searches=Count('id'), last_seen=Max('created_at'))
            .order_by('-searches', '-last_seen')[:20]
        ]
        recent_events = [
            {
                'id': event.id,
                'event_type': event.event_type,
                'source': event.source,
                'query': event.query,
                'result_count': event.result_count,
                'product_id': event.product_id,
                'product_title': event.product_title,
                'order_number': event.order_number,
                'user_email': event.user_email or 'Anonymous',
                'category': event.category,
                'brand': event.brand,
                'created_at': event.created_at,
            }
            for event in events.order_by('-created_at', '-id')[:50]
        ]

        def rate(value):
            return round((value / context_count) * 100, 1) if context_count else 0

        return Response(
            {
                'range': {'days': days, 'start': start.date().isoformat(), 'end': now.date().isoformat()},
                'kpis': {
                    'total_searches': search_events.count(),
                    'image_searches': events.filter(event_type=SearchAnalyticsEvent.EVENT_IMAGE_SEARCH_SUBMITTED).count(),
                    'zero_result_searches': events.filter(event_type=SearchAnalyticsEvent.EVENT_NO_RESULTS).count(),
                    'product_clicks': events.filter(event_type=SearchAnalyticsEvent.EVENT_PRODUCT_CLICKED).count(),
                    'search_contexts': context_count,
                    'cart_conversions': cart_contexts,
                    'order_conversions': order_contexts,
                    'search_to_cart_rate': rate(cart_contexts),
                    'search_to_order_rate': rate(order_contexts),
                },
                'top_terms': top_terms,
                'zero_result_terms': zero_result_terms,
                'clicked_products': clicked_products,
                'user_searches': user_searches,
                'recent_events': recent_events,
            }
        )


class AdminCampaignsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        Line = get_model('order', 'Line')
        Product = get_model('catalogue', 'Product')
        StockRecord = get_model('partner', 'StockRecord')
        User = get_user_model()

        AuditLog = None
        try:
            from apps.auditlog.models import AuditLog as AuditLogModel

            AuditLog = AuditLogModel
        except Exception:
            AuditLog = None

        now = timezone.now()
        days = min(max(int(request.query_params.get('days', 30) or 30), 1), 365)
        start = now - timedelta(days=days - 1)

        orders = Order.objects.all()
        recent_orders = orders.filter(date_placed__date__gte=start.date())
        total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
        active_customers = recent_orders.exclude(user=None).values('user_id').distinct().count()
        quote_leads = (
            AuditLog.objects.filter(event_type='quotes.requested', created_at__date__gte=start.date()).count()
            if AuditLog
            else 0
        )
        new_customers = User.objects.filter(date_joined__date__gte=start.date(), is_staff=False).count()

        popular_rows = (
            Line.objects.exclude(product_id=None)
            .filter(order__date_placed__date__gte=start.date())
            .values('product_id', 'product__title')
            .annotate(quantity=Sum('quantity'), revenue=Sum('line_price_incl_tax'))
            .order_by('-quantity')[:6]
        )
        product_ids = [row['product_id'] for row in popular_rows]
        products = {
            product.id: product
            for product in Product.objects.filter(id__in=product_ids).prefetch_related('categories', 'stockrecords')
        }
        product_opportunities = []
        for row in popular_rows:
            product = products.get(row['product_id'])
            stock = _available_stock_for_product(product)
            product_opportunities.append(
                {
                    'id': row['product_id'],
                    'name': row['product__title'] or getattr(product, 'title', ''),
                    'category': _product_category_name(product),
                    'units_sold': row['quantity'] or 0,
                    'revenue': _decimal_to_float(row.get('revenue')),
                    'stock': stock,
                    'signal': 'Restock before promotion' if stock < 10 else 'Promote',
                }
            )

        low_stock_count = (
            StockRecord.objects.values('product_id')
            .annotate(total_stock=Sum('num_in_stock'))
            .filter(total_stock__gt=0, total_stock__lt=10)
            .count()
        )
        draft_products = Product.objects.filter(is_public=False).count()
        pending_orders = orders.filter(status__in=['Pending', 'Processing', 'Packed']).count()

        campaigns = [
            {
                'id': 'quote-follow-up',
                'name': 'Quote lead follow-up',
                'status': 'ready' if quote_leads else 'watching',
                'audience': quote_leads,
                'channel': 'Email / Sales call',
                'priority': 'High' if quote_leads else 'Medium',
                'description': 'Contact customers who submitted quote requests in the selected window.',
            },
            {
                'id': 'pending-order-nudge',
                'name': 'Pending order nudge',
                'status': 'ready' if pending_orders else 'watching',
                'audience': pending_orders,
                'channel': 'Email / WhatsApp',
                'priority': 'High' if pending_orders else 'Low',
                'description': 'Follow up orders still waiting for processing, payment, packing, or shipment.',
            },
            {
                'id': 'stock-clearance',
                'name': 'Low-stock clearance',
                'status': 'review',
                'audience': low_stock_count,
                'channel': 'Storefront banner',
                'priority': 'Medium',
                'description': 'Promote products with low but available stock, after validating supplier replenishment.',
            },
            {
                'id': 'catalog-readiness',
                'name': 'Draft product launch',
                'status': 'blocked' if draft_products else 'complete',
                'audience': draft_products,
                'channel': 'Admin task',
                'priority': 'Medium' if draft_products else 'Low',
                'description': 'Review unpublished products and prepare launch content before front-end promotion.',
            },
        ]

        return Response(
            {
                'range': {'days': days, 'start': start.date(), 'end': now.date()},
                'kpis': {
                    'total_customers': total_customers,
                    'active_customers': active_customers,
                    'new_customers': new_customers,
                    'quote_leads': quote_leads,
                    'pending_orders': pending_orders,
                    'draft_products': draft_products,
                },
                'campaigns': campaigns,
                'product_opportunities': product_opportunities,
            }
        )


class AdminSupportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        EmailNotification = None
        try:
            from apps.notifications.models import EmailNotification as EmailNotificationModel

            EmailNotification = EmailNotificationModel
        except Exception:
            EmailNotification = None

        page_size = min(max(int(request.query_params.get('page_size', 25) or 25), 1), 100)

        quote_notifications = []
        if EmailNotification:
            quote_notifications = list(
                EmailNotification.objects.filter(event_type__in=['quote_request_customer', 'quote_request_internal'])
                .order_by('-created_at')[:page_size]
            )

        order_cases = list(
            Order.objects.select_related('user')
            .filter(Q(status__in=['Pending', 'Processing', 'Packed', 'Failed', 'Cancelled', 'Canceled']) | Q(status=''))
            .order_by('-date_placed', '-id')[:page_size]
        )

        tickets = []
        for notification in quote_notifications[:10]:
            metadata = notification.metadata or {}
            tickets.append(
                {
                    'id': f'notification-{notification.id}',
                    'type': 'quote',
                    'customer': metadata.get('name') or notification.recipient or 'Quote lead',
                    'contact': metadata.get('email') or notification.recipient,
                    'subject': notification.subject,
                    'message': metadata.get('company') or 'Quote request notification generated.',
                    'status': notification.status,
                    'source': 'Quote request',
                    'reference': notification.related_object_id or '',
                    'created_at': notification.created_at,
                }
            )

        for order in order_cases[:15]:
            status_label = order.status or 'Pending'
            tickets.append(
                {
                    'id': f'order-{order.id}',
                    'type': 'order',
                    'customer': _order_customer_name(order),
                    'contact': getattr(order.user, 'email', '') if getattr(order, 'user_id', None) else order.guest_email,
                    'subject': f'Order {order.number} needs attention',
                    'message': f'Current order status is {status_label}.',
                    'status': status_label,
                    'source': 'Order operations',
                    'reference': order.number,
                    'created_at': order.date_placed,
                }
            )

        tickets.sort(key=lambda item: item['created_at'], reverse=True)
        tickets = tickets[:page_size]

        failed_notifications = (
            EmailNotification.objects.filter(status='failed').count()
            if EmailNotification
            else 0
        )

        return Response(
            {
                'kpis': {
                    'open_cases': len(tickets),
                    'quote_cases': len([ticket for ticket in tickets if ticket['type'] == 'quote']),
                    'order_cases': len([ticket for ticket in tickets if ticket['type'] == 'order']),
                    'failed_notifications': failed_notifications,
                },
                'tickets': tickets,
            }
        )
