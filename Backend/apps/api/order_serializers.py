import re
from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

from .checkout_utils import (
    basket_currency,
    basket_subtotal_excl_tax,
    get_checkout_session,
    get_selected_shipping_method,
    get_shipping_address,
    shipping_charge_for_method,
    shipping_country_code,
)

ADMIN_ORDER_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Packed', 'Packed'),
    ('Paid', 'Paid'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
    ('Failed', 'Failed'),
]


def _order_primary_image_url(product) -> str:
    if not product:
        return ''
    try:
        primary = product.primary_image()
    except TypeError:
        primary = product.primary_image
    except Exception:
        primary = None

    if primary and getattr(primary, 'original', None):
        return primary.original.url or ''
    return ''


def _order_customer_name(order) -> str:
    user = getattr(order, 'user', None)
    if user and callable(getattr(user, 'get_full_name', None)):
        full_name = (user.get_full_name() or '').strip()
        if full_name:
            return full_name
    shipping_address = getattr(order, 'shipping_address', None)
    if shipping_address:
        first_name = (getattr(shipping_address, 'first_name', '') or '').strip()
        last_name = (getattr(shipping_address, 'last_name', '') or '').strip()
        full_name = ' '.join(part for part in [first_name, last_name] if part).strip()
        if full_name:
            return full_name
    if user:
        return (getattr(user, 'username', '') or getattr(user, 'email', '') or '').strip()
    return (order.guest_email or '').strip() or 'Guest Customer'


def _order_company_name(order) -> str:
    user = getattr(order, 'user', None)
    profile = getattr(user, 'customer_profile', None) if user else None
    company = (getattr(profile, 'company', '') or '').strip() if profile else ''
    if company:
        return company
    shipping_address = getattr(order, 'shipping_address', None)
    line3 = (getattr(shipping_address, 'line3', '') or '').strip() if shipping_address else ''
    line4 = (getattr(shipping_address, 'line4', '') or '').strip() if shipping_address else ''
    if line3:
        return line3
    if line4:
        return line4
    return _order_customer_name(order)


def _order_status_flags(order) -> dict:
    status_value = (order.status or '').strip().lower()
    packaged = status_value in {'packed', 'shipped', 'delivered', 'complete', 'completed'}
    fulfilled = status_value in {'shipped', 'delivered', 'complete', 'completed'}
    paid = bool(getattr(order, 'sources', None) and order.sources.exists()) or status_value in {'paid', 'complete', 'completed', 'delivered'}
    invoiced = paid or status_value in {'processing', 'packed', 'shipped', 'delivered', 'complete', 'completed'}
    return {
        'packaged': packaged,
        'fulfilled': fulfilled,
        'invoiced': invoiced,
        'paid': paid,
    }


def _order_tracking_timeline(order) -> list[dict]:
    timeline = []
    for change in order.status_changes.order_by('date_created'):
        timeline.append(
            {
                'status': change.new_status or order.status or 'Pending',
                'date': change.date_created,
                'location': order.shipping_method or 'Order workflow',
            }
        )

    if not timeline:
        timeline.append(
            {
                'status': order.status or 'Pending',
                'date': order.date_placed,
                'location': order.shipping_method or 'Order workflow',
            }
        )
    return timeline


def _order_last_updated(order):
    latest_change = order.status_changes.order_by('-date_created').first()
    return getattr(latest_change, 'date_created', None) or order.date_placed


def _order_primary_tracking_reference(order) -> str:
    supplier_groups = getattr(order, 'supplier_groups', None)
    if supplier_groups is None:
        supplier_groups = order.supplier_groups.all()
    elif hasattr(supplier_groups, 'all'):
        supplier_groups = supplier_groups.all()
    for group in supplier_groups:
        reference = (getattr(group, 'tracking_reference', '') or '').strip()
        if reference:
            return reference
    latest_event = order.shipping_events.order_by('-date_created').first() if hasattr(order, 'shipping_events') else None
    notes = (getattr(latest_event, 'notes', '') or '').strip()
    if notes:
        match = re.search(r'Tracking:\s*([^\.\n]+)', notes)
        if match:
            return match.group(1).strip()
    return ''


class SupplierGroupSerializer(serializers.Serializer):
    def to_representation(self, group):
        return {
            'id': group.id,
            'partner': {
                'id': group.partner_id,
                'name': group.partner.name,
                'code': group.partner.code,
            },
            'status': group.status,
            'line_count': group.line_count,
            'item_count': group.item_count,
            'total_excl_tax': float(group.total_excl_tax or Decimal('0.00')),
            'total_incl_tax': float(group.total_incl_tax or Decimal('0.00')),
            'shipping_excl_tax': float(group.shipping_excl_tax or Decimal('0.00')),
            'shipping_incl_tax': float(group.shipping_incl_tax or Decimal('0.00')),
            'tracking_reference': group.tracking_reference or '',
            'notes': group.notes or '',
        }


class OrderPlacementSerializer(serializers.Serializer):
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    payment_reference = serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate(self, attrs):
        request = self.context['request']
        basket = request.basket
        shipping_address = get_shipping_address(request, basket)
        shipping_method = get_selected_shipping_method(request, basket, shipping_address=shipping_address)
        payment_reference = (attrs.get('payment_reference') or '').strip()

        if basket.is_empty:
            raise serializers.ValidationError({'basket': 'Your basket is empty.'})

        if basket.is_shipping_required() and not shipping_address:
            raise serializers.ValidationError({'shipping_address': 'Shipping address is required before placing an order.'})

        if basket.is_shipping_required() and not shipping_method:
            raise serializers.ValidationError({'shipping_method': 'Select a shipping method before placing an order.'})

        guest_email = (attrs.get('guest_email') or '').strip().lower()
        if request.user.is_authenticated:
            guest_email = ''
            if not (request.user.email or '').strip():
                raise serializers.ValidationError({'account': 'Authenticated users must have an email address to place an order.'})
        elif settings.OSCAR_ALLOW_ANON_CHECKOUT:
            if not guest_email:
                guest_email = (get_checkout_session(request).get_guest_email() or '').strip().lower()
            if not guest_email:
                raise serializers.ValidationError({'guest_email': 'Guest email is required to place an order.'})
        else:
            raise serializers.ValidationError({'account': 'Authentication is required to place an order.'})

        attrs['guest_email'] = guest_email
        attrs['shipping_address'] = shipping_address
        attrs['shipping_method'] = shipping_method
        attrs['payment_reference'] = payment_reference
        return attrs


class OrderLineSerializer(serializers.Serializer):
    def to_representation(self, line):
        return {
            'id': line.id,
            'title': line.title,
            'upc': line.upc,
            'quantity': line.quantity,
            'partner_name': line.partner_name,
            'partner_sku': line.partner_sku,
            'status': line.status,
            'unit_price_excl_tax': float(line.unit_price_excl_tax or Decimal('0.00')),
            'unit_price_incl_tax': float(line.unit_price_incl_tax or Decimal('0.00')),
            'line_price_excl_tax': float(line.line_price_excl_tax or Decimal('0.00')),
            'line_price_incl_tax': float(line.line_price_incl_tax or Decimal('0.00')),
            'currency': line.order.currency,
        }


class OrderSummarySerializer(serializers.Serializer):
    def to_representation(self, order):
        shipping_address = getattr(order, 'shipping_address', None)
        supplier_groups = getattr(order, 'supplier_groups', None)
        if supplier_groups is None:
            supplier_groups = order.supplier_groups.select_related('partner').all()
        return {
            'id': order.id,
            'number': order.number,
            'status': order.status,
            'currency': order.currency,
            'guest_email': order.guest_email or '',
            'date_placed': order.date_placed,
            'shipping_method': order.shipping_method,
            'shipping_code': order.shipping_code,
            'totals': {
                'total_excl_tax': float(order.total_excl_tax or Decimal('0.00')),
                'total_incl_tax': float(order.total_incl_tax or Decimal('0.00')),
                'shipping_excl_tax': float(order.shipping_excl_tax or Decimal('0.00')),
                'shipping_incl_tax': float(order.shipping_incl_tax or Decimal('0.00')),
                'tax': float((order.total_incl_tax or Decimal('0.00')) - (order.total_excl_tax or Decimal('0.00'))),
            },
            'tax_code': getattr(order, 'tax_code', '') or '',
            'shipping_address': {
                'first_name': getattr(shipping_address, 'first_name', '') or '',
                'last_name': getattr(shipping_address, 'last_name', '') or '',
                'line1': getattr(shipping_address, 'line1', '') or '',
                'line2': getattr(shipping_address, 'line2', '') or '',
                'line3': getattr(shipping_address, 'line3', '') or '',
                'line4': getattr(shipping_address, 'line4', '') or '',
                'state': getattr(shipping_address, 'state', '') or '',
                'postcode': getattr(shipping_address, 'postcode', '') or '',
                'country_code': shipping_country_code(shipping_address),
                'phone_number': str(getattr(shipping_address, 'phone_number', '') or ''),
                'notes': getattr(shipping_address, 'notes', '') or '',
            }
            if shipping_address
            else None,
            'lines': OrderLineSerializer(order.lines.select_related('partner', 'stockrecord', 'product').all(), many=True).data,
            'supplier_groups': SupplierGroupSerializer(supplier_groups, many=True).data,
        }


class OrderListSerializer(serializers.Serializer):
    def to_representation(self, order):
        line_count = getattr(order, 'line_count', None)
        item_count = getattr(order, 'item_count', None)
        if item_count is None:
            item_count = sum(line.quantity for line in order.lines.all())

        return {
            'id': order.id,
            'number': order.number,
            'status': order.status,
            'currency': order.currency,
            'date_placed': order.date_placed,
            'line_count': line_count if line_count is not None else order.lines.count(),
            'item_count': item_count,
            'total_incl_tax': float(order.total_incl_tax or Decimal('0.00')),
            'shipping_incl_tax': float(order.shipping_incl_tax or Decimal('0.00')),
            'supplier_group_count': order.supplier_groups.count() if hasattr(order, 'supplier_groups') else 0,
        }


class OrderStatusSerializer(serializers.Serializer):
    def to_representation(self, order):
        changes = []
        for change in order.status_changes.order_by('date_created'):
            changes.append(
                {
                    'old_status': change.old_status or '',
                    'new_status': change.new_status or '',
                    'date_created': change.date_created,
                }
            )

        timeline = []
        if not changes:
            timeline.append({'status': order.status, 'date_created': order.date_placed})
        else:
            for change in changes:
                timeline.append({'status': change['new_status'], 'date_created': change['date_created']})

        return {
            'number': order.number,
            'status': order.status,
            'date_placed': order.date_placed,
            'shipping_method': order.shipping_method,
            'shipping_code': order.shipping_code,
            'timeline': timeline,
        }


class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ADMIN_ORDER_STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    tracking_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate(self, attrs):
        attrs['note'] = (attrs.get('note') or '').strip()
        attrs['tracking_reference'] = (attrs.get('tracking_reference') or '').strip()
        return attrs


class AdminOrderListSerializer(serializers.Serializer):
    def to_representation(self, order):
        flags = _order_status_flags(order)
        return {
            'id': order.id,
            'orderNo': order.number,
            'companyName': _order_company_name(order),
            'customerName': _order_customer_name(order),
            'status': order.status or 'Pending',
            'packaged': flags['packaged'],
            'fulfilled': flags['fulfilled'],
            'invoiced': flags['invoiced'],
            'paid': flags['paid'],
            'orderTotal': float(order.total_incl_tax or Decimal('0.00')),
            'createdDate': order.date_placed,
            'lastUpdated': _order_last_updated(order),
        }


class AdminOrderDetailSerializer(serializers.Serializer):
    def to_representation(self, order):
        flags = _order_status_flags(order)
        shipping_address = getattr(order, 'shipping_address', None)
        customer_email = (getattr(getattr(order, 'user', None), 'email', '') or order.guest_email or '').strip()
        customer_phone = ''
        profile = getattr(getattr(order, 'user', None), 'customer_profile', None)
        if profile and getattr(profile, 'phone', None):
            customer_phone = str(profile.phone or '').strip()
        if not customer_phone and shipping_address:
            customer_phone = str(getattr(shipping_address, 'phone_number', '') or '').strip()

        return {
            'id': order.id,
            'orderNo': order.number,
            'companyName': _order_company_name(order),
            'customerName': _order_customer_name(order),
            'status': order.status or 'Pending',
            'packaged': flags['packaged'],
            'fulfilled': flags['fulfilled'],
            'invoiced': flags['invoiced'],
            'paid': flags['paid'],
            'orderTotal': float(order.total_incl_tax or Decimal('0.00')),
            'createdDate': order.date_placed,
            'lastUpdated': _order_last_updated(order),
            'orderVia': 'Web',
            'trackingReference': _order_primary_tracking_reference(order),
            'availableStatuses': [choice[0] for choice in ADMIN_ORDER_STATUS_CHOICES],
            'shippingAddress': {
                'street': ' '.join(part for part in [
                    getattr(shipping_address, 'line1', '') or '',
                    getattr(shipping_address, 'line2', '') or '',
                ] if part).strip(),
                'city': getattr(shipping_address, 'line4', '') or '',
                'state': getattr(shipping_address, 'state', '') or '',
                'zipCode': getattr(shipping_address, 'postcode', '') or '',
            } if shipping_address else None,
            'subtotal': float((order.total_excl_tax or Decimal('0.00')) - (order.shipping_excl_tax or Decimal('0.00'))),
            'shipping': float(order.shipping_incl_tax or Decimal('0.00')),
            'tax': float((order.total_incl_tax or Decimal('0.00')) - (order.total_excl_tax or Decimal('0.00'))),
            'products': [
                {
                    'id': line.id,
                    'quantity': line.quantity,
                    'name': line.title,
                    'image': _order_primary_image_url(getattr(line, 'product', None)),
                    'price': float(line.line_price_incl_tax or Decimal('0.00')),
                }
                for line in order.lines.select_related('product').all()
            ],
            'tracking': _order_tracking_timeline(order),
            'supplierGroups': [
                {
                    'id': group.id,
                    'name': group.partner.name,
                    'status': group.status,
                    'trackingReference': group.tracking_reference or '',
                    'notes': group.notes or '',
                    'lineCount': group.line_count,
                    'itemCount': group.item_count,
                }
                for group in order.supplier_groups.select_related('partner').all()
            ],
            'customer': {
                'name': _order_customer_name(order),
                'company': _order_company_name(order),
                'email': customer_email,
                'phone': customer_phone,
            },
        }


def build_order_prices(basket, shipping_address, shipping_method):
    from oscar.core.prices import Price

    from apps.common.taxes import calculate_checkout_taxes

    subtotal_excl_tax = basket_subtotal_excl_tax(basket)
    shipping_excl_tax = shipping_charge_for_method(shipping_method, basket)
    country_code = shipping_country_code(shipping_address)

    tax_breakdown = calculate_checkout_taxes(
        subtotal_excl_tax,
        shipping_excl_tax,
        country_code,
        basket=basket,
        shipping_method=shipping_method,
    )
    merchandise_tax = Decimal(str(tax_breakdown['merchandise_tax']))
    shipping_tax = Decimal(str(tax_breakdown['shipping_tax']))

    shipping_price = Price(
        currency=basket_currency(basket),
        excl_tax=shipping_excl_tax,
        incl_tax=shipping_excl_tax + shipping_tax,
        tax_code=f'{country_code or "XX"}-shipping',
    )
    order_total = Price(
        currency=basket_currency(basket),
        excl_tax=subtotal_excl_tax + shipping_excl_tax,
        incl_tax=subtotal_excl_tax + shipping_excl_tax + merchandise_tax + shipping_tax,
        tax_code=f'{country_code or "XX"}-{tax_breakdown.get("shipping_profile") or "order"}',
    )

    return {
        'shipping_price': shipping_price,
        'order_total': order_total,
        'tax_breakdown': tax_breakdown,
    }
