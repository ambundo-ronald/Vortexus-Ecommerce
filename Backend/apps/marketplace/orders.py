from collections import defaultdict
from decimal import Decimal

from django.apps import apps


ZERO = Decimal('0.00')


def ensure_supplier_order_groups(order):
    SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')
    SupplierOrderLineAllocation = apps.get_model('marketplace', 'SupplierOrderLineAllocation')
    SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
    SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
    Line = apps.get_model('order', 'Line')

    lines = list(
        Line.objects.filter(order=order)
        .select_related('partner', 'product', 'stockrecord')
        .order_by('id')
    )
    if not lines:
        SupplierOrderGroup.objects.filter(order=order).delete()
        SupplierOrderLineAllocation.objects.filter(order=order).delete()
        return []

    groups = defaultdict(list)
    for line in lines:
        if line.partner_id:
            groups[line.partner_id].append(line)

    total_lines_incl = sum((line.line_price_incl_tax or ZERO) for line in lines) or ZERO
    total_lines_excl = sum((line.line_price_excl_tax or ZERO) for line in lines) or ZERO

    existing = {group.partner_id: group for group in SupplierOrderGroup.objects.filter(order=order).select_related('partner')}
    existing_allocations = {
        allocation.line_id: allocation
        for allocation in SupplierOrderLineAllocation.objects.filter(order=order)
        .select_related('supplier_offer', 'supplier')
    }
    seen_partner_ids = set()
    seen_line_ids = set()
    created_groups = []

    for partner_id, partner_lines in groups.items():
        partner = partner_lines[0].partner
        seen_partner_ids.add(partner_id)

        lines_incl = sum((line.line_price_incl_tax or ZERO) for line in partner_lines)
        lines_excl = sum((line.line_price_excl_tax or ZERO) for line in partner_lines)
        shipping_incl = _allocate_amount(order.shipping_incl_tax or ZERO, lines_incl, total_lines_incl)
        shipping_excl = _allocate_amount(order.shipping_excl_tax or ZERO, lines_excl, total_lines_excl)
        status = _recompute_supplier_group_status_from_lines(partner_lines)

        group = existing.get(partner_id)
        if group is None:
            group = SupplierOrderGroup(order=order, partner=partner)

        group.status = status
        group.line_count = len(partner_lines)
        group.item_count = sum(line.quantity for line in partner_lines)
        group.total_excl_tax = lines_excl
        group.total_incl_tax = lines_incl
        group.shipping_excl_tax = shipping_excl
        group.shipping_incl_tax = shipping_incl
        group.save()
        created_groups.append(group)

        supplier_profile = SupplierProfile.objects.filter(partner_id=partner_id).first()
        offer_map = {
            offer.product_id: offer
            for offer in SupplierProductOffer.objects.filter(
                supplier=supplier_profile,
                product_id__in=[line.product_id for line in partner_lines if line.product_id],
                status=SupplierProductOffer.STATUS_APPROVED,
            ).select_related('stockrecord')
        } if supplier_profile else {}

        for line in partner_lines:
            seen_line_ids.add(line.id)
            offer = offer_map.get(line.product_id)
            supplier_unit_cost = _supplier_unit_cost_for_line(line, offer)
            quantity = int(line.quantity or 0)
            supplier_total = (supplier_unit_cost * Decimal(quantity)).quantize(Decimal('0.01'))
            customer_unit_excl = Decimal(str(line.unit_price_excl_tax or ZERO)).quantize(Decimal('0.01'))
            customer_unit_incl = Decimal(str(line.unit_price_incl_tax or ZERO)).quantize(Decimal('0.01'))
            customer_line_excl = line.line_price_excl_tax or ZERO
            gross_margin = (customer_line_excl - supplier_total).quantize(Decimal('0.01'))
            allocation = existing_allocations.get(line.id) or SupplierOrderLineAllocation(order=order, line=line)
            allocation.partner = partner
            allocation.supplier = supplier_profile
            allocation.product = line.product
            allocation.stockrecord = line.stockrecord
            allocation.supplier_offer = offer
            allocation.quantity = quantity
            allocation.customer_unit_price_excl_tax = customer_unit_excl
            allocation.customer_unit_price_incl_tax = customer_unit_incl
            allocation.supplier_unit_cost = supplier_unit_cost
            allocation.supplier_total_cost = supplier_total
            allocation.gross_margin = gross_margin
            allocation.currency = order.currency or getattr(line.stockrecord, 'price_currency', '') or 'KES'
            allocation.save()

    SupplierOrderGroup.objects.filter(order=order).exclude(partner_id__in=seen_partner_ids).delete()
    SupplierOrderLineAllocation.objects.filter(order=order).exclude(line_id__in=seen_line_ids).delete()
    return created_groups


def update_supplier_group_tracking(order, partner_id: int, *, tracking_reference: str = '', note: str = ''):
    SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')
    group = SupplierOrderGroup.objects.filter(order=order, partner_id=partner_id).first()
    if group is None:
        groups = ensure_supplier_order_groups(order)
        group = next((item for item in groups if item.partner_id == partner_id), None)
        if group is None:
            return None

    if tracking_reference:
        group.tracking_reference = tracking_reference
    if note:
        group.notes = note
    group.save(update_fields=['tracking_reference', 'notes', 'updated_at'])
    return group


def _allocate_amount(amount, part, whole):
    amount = Decimal(str(amount or ZERO))
    part = Decimal(str(part or ZERO))
    whole = Decimal(str(whole or ZERO))
    if whole <= ZERO:
        return ZERO
    return (amount * part / whole).quantize(Decimal('0.01'))


def _unit_amount(amount, quantity):
    amount = Decimal(str(amount or ZERO))
    quantity = Decimal(str(quantity or 0))
    if quantity <= ZERO:
        return ZERO
    return (amount / quantity).quantize(Decimal('0.01'))


def _supplier_unit_cost_for_line(line, offer):
    if offer and offer.supplier_unit_cost is not None:
        return Decimal(str(offer.supplier_unit_cost or ZERO)).quantize(Decimal('0.01'))
    stock_price = getattr(getattr(line, 'stockrecord', None), 'price', None)
    if stock_price is not None:
        return Decimal(str(stock_price)).quantize(Decimal('0.01'))
    return _unit_amount(line.line_price_excl_tax, line.quantity)


def _recompute_supplier_group_status_from_lines(lines):
    statuses = {((line.status or '').strip().lower() or 'pending') for line in lines}

    if statuses == {'delivered'}:
        return 'delivered'
    if statuses == {'cancelled'}:
        return 'cancelled'
    if statuses.issubset({'shipped', 'delivered'}):
        return 'shipped'
    if 'shipped' in statuses or 'delivered' in statuses:
        return 'partially_shipped'
    if statuses == {'packed'}:
        return 'packed'
    if 'packed' in statuses:
        return 'processing'
    if statuses == {'processing'}:
        return 'processing'
    return 'pending'
