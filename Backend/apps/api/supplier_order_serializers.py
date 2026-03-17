from rest_framework import serializers


SUPPLIER_LINE_STATUS_CHOICES = [
    ('processing', 'Processing'),
    ('packed', 'Packed'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]


class SupplierOrderLineStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SUPPLIER_LINE_STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    tracking_reference = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate(self, attrs):
        attrs['note'] = (attrs.get('note') or '').strip()
        attrs['tracking_reference'] = (attrs.get('tracking_reference') or '').strip()
        return attrs


class SupplierOrderListSerializer(serializers.Serializer):
    def to_representation(self, group):
        order = group.order
        return {
            'group_id': group.id,
            'number': order.number,
            'status': group.status,
            'order_status': order.status,
            'date_placed': order.date_placed,
            'currency': order.currency,
            'customer': {
                'name': ' '.join(part for part in [getattr(order.user, 'first_name', ''), getattr(order.user, 'last_name', '')] if part).strip(),
                'email': order.user.email if getattr(order, 'user_id', None) else order.guest_email,
            },
            'supplier': {
                'partner_id': group.partner_id,
                'partner_name': group.partner.name,
                'partner_code': group.partner.code,
            },
            'supplier_line_count': group.line_count,
            'supplier_item_count': group.item_count,
            'supplier_total_incl_tax': float(group.total_incl_tax or 0),
            'supplier_shipping_incl_tax': float(group.shipping_incl_tax or 0),
            'tracking_reference': group.tracking_reference or '',
        }


class SupplierOrderDetailSerializer(serializers.Serializer):
    def to_representation(self, group):
        order = group.order
        supplier_profile = self.context['supplier_profile']
        supplier_lines = []
        for line in order.lines.all():
            if line.partner_id != supplier_profile.partner_id:
                continue
            supplier_lines.append(
                {
                    'id': line.id,
                    'title': line.title,
                    'upc': line.upc,
                    'quantity': line.quantity,
                    'partner_sku': line.partner_sku,
                    'status': line.status,
                    'unit_price_incl_tax': float(line.unit_price_incl_tax or 0),
                    'line_price_incl_tax': float(line.line_price_incl_tax or 0),
                }
            )

        shipping_address = getattr(order, 'shipping_address', None)
        return {
            'group_id': group.id,
            'number': order.number,
            'status': group.status,
            'order_status': order.status,
            'date_placed': order.date_placed,
            'currency': order.currency,
            'customer': {
                'name': ' '.join(part for part in [getattr(order.user, 'first_name', ''), getattr(order.user, 'last_name', '')] if part).strip(),
                'email': order.user.email if getattr(order, 'user_id', None) else order.guest_email,
            },
            'supplier': {
                'partner_id': group.partner_id,
                'partner_name': group.partner.name,
                'partner_code': group.partner.code,
            },
            'shipping_method': order.shipping_method,
            'shipping_code': order.shipping_code,
            'tracking_reference': group.tracking_reference or '',
            'notes': group.notes or '',
            'supplier_totals': {
                'line_count': group.line_count,
                'item_count': group.item_count,
                'total_excl_tax': float(group.total_excl_tax or 0),
                'total_incl_tax': float(group.total_incl_tax or 0),
                'shipping_excl_tax': float(group.shipping_excl_tax or 0),
                'shipping_incl_tax': float(group.shipping_incl_tax or 0),
            },
            'shipping_address': {
                'first_name': getattr(shipping_address, 'first_name', '') or '',
                'last_name': getattr(shipping_address, 'last_name', '') or '',
                'line1': getattr(shipping_address, 'line1', '') or '',
                'line2': getattr(shipping_address, 'line2', '') or '',
                'line3': getattr(shipping_address, 'line3', '') or '',
                'line4': getattr(shipping_address, 'line4', '') or '',
                'state': getattr(shipping_address, 'state', '') or '',
                'postcode': getattr(shipping_address, 'postcode', '') or '',
                'phone_number': str(getattr(shipping_address, 'phone_number', '') or ''),
                'notes': getattr(shipping_address, 'notes', '') or '',
            }
            if shipping_address
            else None,
            'lines': supplier_lines,
        }
