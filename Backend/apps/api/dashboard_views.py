from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from oscar.core.loading import get_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.models import AuditLog, SearchAnalyticsEvent
from apps.common.products import stockrecord_count
from apps.notifications.models import CallbackRequest


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


def _metadata_value(metadata, key, default=''):
    if not isinstance(metadata, dict):
        return default
    value = metadata.get(key, default)
    return value if value not in (None, '') else default


def _session_key(row):
    metadata = row.get('metadata') or {}
    anonymous_id = str(_metadata_value(metadata, 'anonymous_id', '')).strip()
    if anonymous_id:
        return f'anon:{anonymous_id}'
    actor_email = str(row.get('actor_email') or '').strip().lower()
    if actor_email:
        return f'user:{actor_email}'
    return f"event:{row.get('id')}"


def _checkout_step_for_path(path):
    path = str(path or '').split('?', 1)[0].rstrip('/')
    if path.endswith('/checkout/cart'):
        return 'cart'
    if path.endswith('/checkout/shipping'):
        return 'shipping'
    if path.endswith('/checkout/payment'):
        return 'payment'
    if path.endswith('/checkout/review'):
        return 'review'
    if path.endswith('/checkout/confirmation'):
        return 'confirmation'
    return ''


def _rate(part, whole):
    return round((part / whole) * 100, 1) if whole else 0


def _customer_label(row):
    actor_email = str(row.get('actor_email') or '').strip()
    if actor_email:
        return actor_email
    metadata = row.get('metadata') or {}
    anonymous_id = str(_metadata_value(metadata, 'anonymous_id', '')).strip()
    if anonymous_id:
        return f'Anonymous {anonymous_id[-8:]}'
    return 'Anonymous'


def _journey_event_payload(row):
    metadata = row.get('metadata') or {}
    event_type = str(row.get('event_type') or '').replace('storefront.', '')
    path = str(_metadata_value(metadata, 'path', '')).strip()
    product_title = str(_metadata_value(metadata, 'product_title', '')).strip()
    query = str(_metadata_value(metadata, 'search', _metadata_value(metadata, 'query', ''))).strip()
    order_number = str(_metadata_value(metadata, 'order_number', '')).strip()
    label = path or product_title or query or order_number or event_type
    return {
        'event_type': event_type,
        'label': label[:120],
        'path': path[:255],
        'product_title': product_title[:255],
        'query': query[:255],
        'order_number': order_number[:64],
        'created_at': row['created_at'],
    }


def _site_analytics_payload(*, start, now):
    events = AuditLog.objects.filter(
        event_type__startswith='storefront.',
        created_at__date__gte=start.date(),
    )
    page_rows = list(
        events.filter(event_type='storefront.page_view')
        .values('id', 'actor_email', 'metadata', 'created_at')
        .order_by('-created_at')[:5000]
    )
    interaction_rows = list(
        events.exclude(event_type='storefront.page_view')
        .values('id', 'event_type', 'actor_email', 'metadata', 'created_at')
        .order_by('-created_at')[:5000]
    )

    session_paths = {}
    checkout_sessions = {step: set() for step in ['cart', 'shipping', 'payment', 'review', 'confirmation']}
    page_counts = {}
    referrer_counts = {}
    activity = {}
    session_details = {}

    for row in page_rows:
        metadata = row.get('metadata') or {}
        key = _session_key(row)
        path = str(_metadata_value(metadata, 'path', '/')).strip() or '/'
        title = str(_metadata_value(metadata, 'title', '')).strip()
        referrer = str(_metadata_value(metadata, 'referrer', '')).strip()
        session_paths.setdefault(key, set()).add(path)
        detail = session_details.setdefault(
            key,
            {
                'session_key': key,
                'customer': _customer_label(row),
                'first_seen': row['created_at'],
                'last_seen': row['created_at'],
                'first_page': path,
                'last_page': path,
                'page_views': 0,
                'event_count': 0,
                'checkout_step': '',
                'events': [],
            },
        )
        if row['created_at'] < detail['first_seen']:
            detail['first_seen'] = row['created_at']
            detail['first_page'] = path
        if row['created_at'] > detail['last_seen']:
            detail['last_seen'] = row['created_at']
            detail['last_page'] = path
        detail['page_views'] += 1
        detail['event_count'] += 1
        detail['events'].append(_journey_event_payload({'event_type': 'storefront.page_view', **row}))
        page_counts.setdefault(path, {'path': path, 'title': title, 'views': 0, 'sessions': set()})
        page_counts[path]['views'] += 1
        page_counts[path]['sessions'].add(key)
        if referrer:
            referrer_counts[referrer] = referrer_counts.get(referrer, 0) + 1
        step = _checkout_step_for_path(path)
        if step:
            checkout_sessions[step].add(key)

        created_at = row['created_at'].astimezone(timezone.get_current_timezone())
        heat_key = (created_at.weekday(), created_at.hour)
        activity[heat_key] = activity.get(heat_key, 0) + 1

    product_views = {}
    product_view_sessions = set()
    cart_sessions = set()
    order_sessions = set()
    voucher_sessions = set()
    for row in interaction_rows:
        metadata = row.get('metadata') or {}
        key = _session_key(row)
        event_type = row.get('event_type')
        detail = session_details.setdefault(
            key,
            {
                'session_key': key,
                'customer': _customer_label(row),
                'first_seen': row['created_at'],
                'last_seen': row['created_at'],
                'first_page': '',
                'last_page': '',
                'page_views': 0,
                'event_count': 0,
                'checkout_step': '',
                'events': [],
            },
        )
        if row['created_at'] < detail['first_seen']:
            detail['first_seen'] = row['created_at']
        if row['created_at'] > detail['last_seen']:
            detail['last_seen'] = row['created_at']
        detail['event_count'] += 1
        detail['events'].append(_journey_event_payload(row))
        if event_type == 'storefront.product_view':
            product_id = _metadata_value(metadata, 'product_id', '')
            product_title = str(_metadata_value(metadata, 'product_title', f'Product #{product_id}')).strip()
            product_key = str(product_id or product_title)
            product_views.setdefault(
                product_key,
                {'product_id': product_id, 'product_title': product_title, 'views': 0, 'sessions': set()},
            )
            product_views[product_key]['views'] += 1
            product_views[product_key]['sessions'].add(key)
            product_view_sessions.add(key)
        elif event_type == 'storefront.cart_item_added':
            cart_sessions.add(key)
        elif event_type == 'storefront.order_confirmation_viewed':
            order_sessions.add(key)
            checkout_sessions['confirmation'].add(key)
            detail['checkout_step'] = 'Completed'
        elif event_type in {'storefront.voucher_applied', 'storefront.voucher_removed'}:
            voucher_sessions.add(key)

    all_sessions = set(session_paths.keys()) | product_view_sessions | cart_sessions | order_sessions | voucher_sessions
    checkout_started = set().union(
        checkout_sessions['cart'],
        checkout_sessions['shipping'],
        checkout_sessions['payment'],
        checkout_sessions['review'],
        cart_sessions,
    )
    checkout_completed = checkout_sessions['confirmation'] | order_sessions
    dropped_checkout = checkout_started - checkout_completed
    bounced_sessions = {key for key, paths in session_paths.items() if len(paths) <= 1 and key not in cart_sessions and key not in order_sessions}

    top_pages = [
        {
            'path': row['path'],
            'title': row['title'],
            'views': row['views'],
            'sessions': len(row['sessions']),
        }
        for row in sorted(page_counts.values(), key=lambda item: item['views'], reverse=True)[:15]
    ]
    top_product_views = [
        {
            'product_id': row['product_id'],
            'product_title': row['product_title'],
            'views': row['views'],
            'sessions': len(row['sessions']),
        }
        for row in sorted(product_views.values(), key=lambda item: item['views'], reverse=True)[:15]
    ]
    top_referrers = [
        {'referrer': referrer, 'visits': visits}
        for referrer, visits in sorted(referrer_counts.items(), key=lambda item: item[1], reverse=True)[:10]
    ]

    heatmap = [
        {'weekday': weekday, 'hour': hour, 'sessions': activity.get((weekday, hour), 0)}
        for weekday in range(7)
        for hour in range(24)
    ]
    busiest_hours = sorted(heatmap, key=lambda item: item['sessions'], reverse=True)[:8]

    session_count = len(all_sessions)
    checkout_started_count = len(checkout_started)
    checkout_completed_count = len(checkout_completed)
    session_summaries = []
    duration_seconds_total = 0
    duration_session_count = 0
    checkout_step_labels = [
        ('confirmation', 'Completed'),
        ('review', 'Review'),
        ('payment', 'Payment'),
        ('shipping', 'Shipping'),
        ('cart', 'Cart'),
    ]
    for key, detail in session_details.items():
        first_seen = detail['first_seen']
        last_seen = detail['last_seen']
        duration_seconds = max(0, int((last_seen - first_seen).total_seconds()))
        if duration_seconds:
            duration_seconds_total += duration_seconds
            duration_session_count += 1
        if not detail['checkout_step']:
            for step, label in checkout_step_labels:
                if key in checkout_sessions[step]:
                    detail['checkout_step'] = label
                    break
        if not detail['checkout_step'] and key in cart_sessions:
            detail['checkout_step'] = 'Cart'
        events_for_session = sorted(detail['events'], key=lambda item: item['created_at'])
        session_summaries.append(
            {
                'session_key': key,
                'customer': detail['customer'],
                'first_page': detail['first_page'] or '-',
                'last_page': detail['last_page'] or '-',
                'first_seen': first_seen,
                'last_seen': last_seen,
                'duration_seconds': duration_seconds,
                'page_views': detail['page_views'],
                'event_count': detail['event_count'],
                'checkout_step': detail['checkout_step'] or 'Browsing',
                'converted': key in checkout_completed,
                'journey': events_for_session[-10:],
            }
        )
    session_summaries.sort(key=lambda item: item['last_seen'], reverse=True)
    avg_session_duration = round(duration_seconds_total / duration_session_count) if duration_session_count else 0
    return {
        'kpis': {
            'sessions': session_count,
            'page_views': len(page_rows),
            'product_views': sum(row['views'] for row in product_views.values()),
            'cart_sessions': len(cart_sessions),
            'checkout_started': checkout_started_count,
            'checkout_completed': checkout_completed_count,
            'checkout_rate': _rate(checkout_completed_count, session_count),
            'checkout_completion_rate': _rate(checkout_completed_count, checkout_started_count),
            'checkout_dropoff_rate': _rate(len(dropped_checkout), checkout_started_count),
            'bounce_rate': _rate(len(bounced_sessions), len(session_paths)),
            'voucher_sessions': len(voucher_sessions),
            'avg_session_duration_seconds': avg_session_duration,
        },
        'checkout_funnel': [
            {'step': 'Cart', 'sessions': len(checkout_sessions['cart'] | cart_sessions)},
            {'step': 'Shipping', 'sessions': len(checkout_sessions['shipping'])},
            {'step': 'Payment', 'sessions': len(checkout_sessions['payment'])},
            {'step': 'Review', 'sessions': len(checkout_sessions['review'])},
            {'step': 'Completed', 'sessions': checkout_completed_count},
        ],
        'top_pages': top_pages,
        'top_product_views': top_product_views,
        'top_referrers': top_referrers,
        'activity_heatmap': heatmap,
        'busiest_hours': busiest_hours,
        'recent_sessions': session_summaries[:25],
    }


class AdminDashboardAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        Line = get_model('order', 'Line')
        Product = get_model('catalogue', 'Product')
        StockRecord = get_model('partner', 'StockRecord')
        ProductImage = get_model('catalogue', 'ProductImage')
        PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')
        User = get_user_model()

        now = timezone.now()
        days = min(max(int(request.query_params.get('days', 30) or 30), 1), 365)
        start = now - timedelta(days=days - 1)

        orders = Order.objects.all()
        recent_orders = orders.filter(date_placed__date__gte=start.date())
        products = Product.objects.all()
        users = User.objects.all()

        pending_statuses = ['Pending', 'Processing', 'Packed']
        completed_statuses = ['Paid', 'Shipped', 'Delivered', 'Complete', 'Completed']
        failed_statuses = ['Failed', 'Cancelled', 'Canceled', 'Refunded', 'Returned']
        excluded_revenue_statuses = failed_statuses
        revenue_orders = orders.exclude(status__in=excluded_revenue_statuses)
        recent_revenue_orders = recent_orders.exclude(status__in=excluded_revenue_statuses)
        revenue_refund_statuses = [
            PaymentRefundLedger.STATUS_SUBMITTED,
            PaymentRefundLedger.STATUS_SUCCEEDED,
        ]
        revenue_refunds = PaymentRefundLedger.objects.filter(
            order__in=revenue_orders,
            status__in=revenue_refund_statuses,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        recent_revenue_refunds = PaymentRefundLedger.objects.filter(
            order__in=recent_revenue_orders,
            status__in=revenue_refund_statuses,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_revenue = max(
            Decimal('0.00'),
            (revenue_orders.aggregate(total=Sum('total_incl_tax'))['total'] or Decimal('0')) - revenue_refunds,
        )
        recent_revenue = max(
            Decimal('0.00'),
            (recent_revenue_orders.aggregate(total=Sum('total_incl_tax'))['total'] or Decimal('0')) - recent_revenue_refunds,
        )

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
            for row in recent_revenue_orders.annotate(day=TruncDate('date_placed'))
            .values('day')
            .annotate(orders=Count('id'), revenue=Sum('total_incl_tax'))
            .order_by('day')
        }
        daily_refunds = {
            row['day']: row['total'] or Decimal('0')
            for row in PaymentRefundLedger.objects.filter(
                order__in=recent_revenue_orders,
                status__in=revenue_refund_statuses,
            )
            .annotate(day=TruncDate('order__date_placed'))
            .values('day')
            .annotate(total=Sum('amount'))
        }
        daily_series = []
        for offset in range(days):
            day = (start + timedelta(days=offset)).date()
            row = daily_rows.get(day, {})
            net_revenue = max(Decimal('0.00'), (row.get('revenue') or Decimal('0')) - daily_refunds.get(day, Decimal('0')))
            daily_series.append(
                {
                    'date': day.isoformat(),
                    'orders': row.get('orders', 0) or 0,
                    'revenue': _decimal_to_float(net_revenue),
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
            .exclude(order__status__in=excluded_revenue_statuses)
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
                'site_analytics': _site_analytics_payload(start=start, now=now),
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
        payment_notifications = []
        if EmailNotification:
            quote_notifications = list(
                EmailNotification.objects.filter(event_type__in=['quote_request_customer', 'quote_request_internal'])
                .order_by('-created_at')[:page_size]
            )
            payment_notifications = list(
                EmailNotification.objects.filter(event_type='payment_deposit_submitted_internal')
                .order_by('-created_at')[:page_size]
            )

        order_cases = list(
            Order.objects.select_related('user')
            .filter(Q(status__in=['Pending', 'Processing', 'Packed', 'Failed', 'Cancelled', 'Canceled']) | Q(status=''))
            .order_by('-date_placed', '-id')[:page_size]
        )

        tickets = []
        callback_requests = list(
            CallbackRequest.objects.select_related('product', 'user', 'assigned_to')
            .order_by('respond_by', '-created_at')[:page_size]
        )
        now = timezone.now()
        for callback_request in callback_requests:
            tickets.append(
                {
                    'id': f'callback-{callback_request.id}',
                    'callback_id': callback_request.id,
                    'type': 'callback',
                    'customer': callback_request.name,
                    'contact': callback_request.phone_number,
                    'subject': f'Call back about {callback_request.product.title}',
                    'message': callback_request.reason,
                    'status': callback_request.status,
                    'source': 'Product callback',
                    'reference': str(callback_request.product_id),
                    'product_id': callback_request.product_id,
                    'product_title': callback_request.product.title,
                    'respond_by': callback_request.respond_by,
                    'is_overdue': callback_request.status == CallbackRequest.STATUS_PENDING and callback_request.respond_by < now,
                    'staff_notes': callback_request.staff_notes,
                    'assigned_to': callback_request.assigned_to.get_full_name() or callback_request.assigned_to.email if callback_request.assigned_to else '',
                    'created_at': callback_request.created_at,
                }
            )
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
        for notification in payment_notifications[:10]:
            metadata = notification.metadata or {}
            tickets.append(
                {
                    'id': f'payment-{notification.id}',
                    'type': 'payment',
                    'customer': metadata.get('customer_email') or notification.recipient or 'Payment customer',
                    'contact': metadata.get('customer_phone') or metadata.get('customer_email') or notification.recipient,
                    'subject': notification.subject,
                    'message': f"KCB PayBill confirmation {metadata.get('external_reference') or 'submitted'} needs verification.",
                    'status': 'Pending confirmation',
                    'source': 'Payment verification',
                    'reference': metadata.get('payment_reference') or notification.related_object_id or '',
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
                    'callback_leads': len([ticket for ticket in tickets if ticket['type'] == 'callback']),
                    'payment_cases': len([ticket for ticket in tickets if ticket['type'] == 'payment']),
                    'overdue_callbacks': len([ticket for ticket in tickets if ticket.get('is_overdue')]),
                    'failed_notifications': failed_notifications,
                },
                'tickets': tickets,
            }
        )
