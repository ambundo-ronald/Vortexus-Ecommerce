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
