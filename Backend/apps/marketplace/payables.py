from decimal import Decimal
import logging

from django.apps import apps
from django.db import transaction
from django.utils import timezone

from apps.payments.services import ensure_order_finance_clear_for_payout


SUCCESS_PAYMENT_STATUSES = {'authorized', 'paid'}
ZERO = Decimal('0.00')
logger = logging.getLogger(__name__)


def supplier_payable_adjustment_totals(payable, *, include_pending=True):
    SupplierPayableAdjustment = apps.get_model('marketplace', 'SupplierPayableAdjustment')
    active_statuses = {
        SupplierPayableAdjustment.STATUS_APPROVED,
        SupplierPayableAdjustment.STATUS_APPLIED,
    }
    if include_pending:
        active_statuses.add(SupplierPayableAdjustment.STATUS_PENDING_REVIEW)
    totals = {
        SupplierPayableAdjustment.TYPE_DEBIT: ZERO,
        SupplierPayableAdjustment.TYPE_CREDIT: ZERO,
        SupplierPayableAdjustment.TYPE_REVERSAL: ZERO,
    }
    for adjustment in payable.adjustments.filter(status__in=active_statuses):
        totals[adjustment.adjustment_type] = _money(totals.get(adjustment.adjustment_type, ZERO) + _money(adjustment.amount))
    return totals


def supplier_payable_net_total(payable, *, include_pending_adjustments=True):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    SupplierPayableAdjustment = apps.get_model('marketplace', 'SupplierPayableAdjustment')
    if payable.status == SupplierPayableLedger.STATUS_REVERSED:
        return ZERO
    totals = supplier_payable_adjustment_totals(payable, include_pending=include_pending_adjustments)
    net = _money(payable.payable_total) - totals[SupplierPayableAdjustment.TYPE_DEBIT] - totals[SupplierPayableAdjustment.TYPE_REVERSAL]
    net += totals[SupplierPayableAdjustment.TYPE_CREDIT]
    return max(ZERO, _money(net))


def supplier_payable_queryset_net_total(queryset, *, include_pending_adjustments=True):
    return sum((supplier_payable_net_total(payable, include_pending_adjustments=include_pending_adjustments) for payable in queryset), ZERO)


def sync_supplier_payable_for_allocation(allocation):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    status, source_status, reversal_reason = _ledger_status_for_allocation(allocation)
    defaults = {
        'supplier': allocation.supplier,
        'partner': allocation.partner,
        'order': allocation.order,
        'line': allocation.line,
        'product': allocation.product,
        'supplier_offer': allocation.supplier_offer,
        'stockrecord': allocation.stockrecord,
        'quantity': int(allocation.quantity or 0),
        'supplier_unit_cost': _money(allocation.supplier_unit_cost),
        'payable_total': _money(allocation.supplier_total_cost),
        'currency': allocation.currency or getattr(allocation.order, 'currency', '') or 'KES',
        'status': status,
        'source_status': source_status,
        'payout_reference': allocation.payout_reference or '',
        'reversal_reason': reversal_reason,
        'metadata': {
            'allocation_id': allocation.id,
            'order_number': allocation.order.number,
            'line_id': allocation.line_id,
            'line_status': getattr(allocation.line, 'status', '') or '',
            'order_status': getattr(allocation.order, 'status', '') or '',
            'allocation_payout_status': allocation.payout_status,
        },
    }
    ledger, _ = SupplierPayableLedger.objects.update_or_create(
        allocation=allocation,
        defaults=defaults,
    )
    _post_supplier_payable_accounting(ledger)
    return ledger


@transaction.atomic
def sync_supplier_payables_for_order(order):
    SupplierOrderLineAllocation = apps.get_model('marketplace', 'SupplierOrderLineAllocation')
    allocations = (
        SupplierOrderLineAllocation.objects.select_related(
            'supplier',
            'partner',
            'order',
            'line',
            'product',
            'supplier_offer',
            'stockrecord',
        )
        .filter(order=order)
        .order_by('id')
    )
    ledgers = [sync_supplier_payable_for_allocation(allocation) for allocation in allocations]
    return ledgers


def _ledger_status_for_allocation(allocation):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    order_status = str(getattr(allocation.order, 'status', '') or '').strip().lower()
    line_status = str(getattr(allocation.line, 'status', '') or '').strip().lower()
    allocation_status = str(allocation.payout_status or '').strip().lower()

    if allocation_status == 'paid':
        return SupplierPayableLedger.STATUS_PAID, 'allocation_paid', ''
    if allocation_status == 'approved':
        return SupplierPayableLedger.STATUS_APPROVED, 'allocation_approved', ''
    if allocation_status == 'cancelled':
        return SupplierPayableLedger.STATUS_REVERSED, 'allocation_cancelled', 'Supplier allocation was cancelled.'
    if order_status in {'cancelled', 'canceled'} or line_status in {'cancelled', 'canceled'}:
        return SupplierPayableLedger.STATUS_REVERSED, 'order_or_line_cancelled', 'Order or order line was cancelled.'
    if _order_has_confirmed_payment(allocation.order):
        reconciliation_status = _order_reconciliation_status(allocation.order)
        if reconciliation_status and reconciliation_status != 'matched':
            return (
                SupplierPayableLedger.STATUS_ON_HOLD,
                f'payment_reconciliation_{reconciliation_status}',
                'Payment reconciliation must be matched before supplier payout.',
            )
        return SupplierPayableLedger.STATUS_PAYABLE, 'payment_confirmed', ''
    return SupplierPayableLedger.STATUS_PENDING, 'payment_pending', ''


def _order_has_confirmed_payment(order) -> bool:
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    return PaymentSession.objects.filter(order=order, status__in=SUCCESS_PAYMENT_STATUSES).exists()


def _order_reconciliation_status(order) -> str:
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    payment = (
        PaymentSession.objects.filter(order=order, status__in=SUCCESS_PAYMENT_STATUSES)
        .order_by('-paid_at', '-updated_at', '-created_at')
        .first()
    )
    if not payment:
        return ''
    from apps.payments.services import sync_payment_reconciliation

    return sync_payment_reconciliation(payment).status


def _money(value) -> Decimal:
    return Decimal(str(value or ZERO)).quantize(Decimal('0.01'))


def create_supplier_payout_batch(*, payable_ids, created_by=None, payout_method='', notes=''):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    SupplierPayoutBatchEntry = apps.get_model('marketplace', 'SupplierPayoutBatchEntry')

    normalized_ids = sorted({int(payable_id) for payable_id in payable_ids if str(payable_id).strip().isdigit()})
    if not normalized_ids:
        raise ValueError('Select at least one payable row.')

    with transaction.atomic():
        payables = list(
            SupplierPayableLedger.objects.select_for_update()
            .select_related('supplier', 'partner')
            .filter(id__in=normalized_ids)
            .order_by('id')
        )
        if len(payables) != len(normalized_ids):
            raise ValueError('One or more payable rows were not found.')
        allowed_statuses = {SupplierPayableLedger.STATUS_PAYABLE, SupplierPayableLedger.STATUS_APPROVED}
        invalid = [payable.id for payable in payables if payable.status not in allowed_statuses]
        if invalid:
            raise ValueError(f'Payable rows must be payable or approved before batching: {invalid}.')
        already_batched = [payable.id for payable in payables if hasattr(payable, 'payout_batch_entry')]
        if already_batched:
            raise ValueError(f'Payable rows are already in a payout batch: {already_batched}.')
        payout_unsafe = []
        checked_order_ids = set()
        for payable in payables:
            if payable.order_id in checked_order_ids:
                continue
            checked_order_ids.add(payable.order_id)
            try:
                ensure_order_finance_clear_for_payout(payable.order)
            except ValueError as exc:
                payout_unsafe.append(f'{payable.order.number}: {exc}')
        if payout_unsafe:
            raise ValueError(
                'Payable rows cannot be batched until finance reconciliation is clear. '
                + ' | '.join(payout_unsafe)
            )
        zero_net = [payable.id for payable in payables if supplier_payable_net_total(payable) <= ZERO]
        if zero_net:
            raise ValueError(f'Payable rows have no net amount left after returns or refunds: {zero_net}.')

        supplier_ids = {payable.supplier_id for payable in payables}
        partner_ids = {payable.partner_id for payable in payables}
        currencies = {payable.currency for payable in payables}
        if len(supplier_ids) > 1 or len(partner_ids) > 1:
            raise ValueError('Create one payout batch per supplier.')
        if len(currencies) > 1:
            raise ValueError('Create one payout batch per currency.')

        total_amount = sum((supplier_payable_net_total(payable) for payable in payables), ZERO)
        batch = SupplierPayoutBatch.objects.create(
            batch_reference=_next_payout_reference(SupplierPayoutBatch),
            supplier=payables[0].supplier,
            partner=payables[0].partner,
            currency=payables[0].currency or 'KES',
            total_amount=total_amount,
            entry_count=len(payables),
            payout_method=(payout_method or '').strip(),
            notes=(notes or '').strip(),
            created_by=created_by if getattr(created_by, 'is_authenticated', False) else None,
        )
        SupplierPayoutBatchEntry.objects.bulk_create(
            [
                SupplierPayoutBatchEntry(
                    batch=batch,
                    payable=payable,
                    amount=supplier_payable_net_total(payable),
                    currency=payable.currency or batch.currency,
                )
                for payable in payables
            ]
        )
        return batch


def submit_supplier_payout_batch(batch, *, user=None):
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    if batch.status != SupplierPayoutBatch.STATUS_DRAFT:
        raise ValueError('Only draft payout batches can be submitted for approval.')
    batch.status = SupplierPayoutBatch.STATUS_PENDING_APPROVAL
    batch.save(update_fields=['status', 'updated_at'])
    return batch


def approve_supplier_payout_batch(batch, *, user=None):
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    if batch.status not in {SupplierPayoutBatch.STATUS_DRAFT, SupplierPayoutBatch.STATUS_PENDING_APPROVAL}:
        raise ValueError('Only draft or pending approval payout batches can be approved.')
    with transaction.atomic():
        batch.status = SupplierPayoutBatch.STATUS_APPROVED
        batch.approved_by = user if getattr(user, 'is_authenticated', False) else None
        batch.approved_at = timezone.now()
        batch.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        SupplierPayableLedger.objects.filter(payout_batch_entry__batch=batch).update(status=SupplierPayableLedger.STATUS_APPROVED)
    return batch


def mark_supplier_payout_batch_paid(batch, *, user=None, payout_reference='', evidence_url='', evidence_file=None):
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    if batch.status != SupplierPayoutBatch.STATUS_APPROVED:
        raise ValueError('Only approved payout batches can be marked paid.')
    reference = (payout_reference or batch.payout_reference or batch.batch_reference).strip()
    with transaction.atomic():
        batch.status = SupplierPayoutBatch.STATUS_PAID
        batch.payout_reference = reference
        if evidence_url:
            batch.evidence_url = evidence_url.strip()
        if evidence_file:
            batch.evidence_file = evidence_file
        batch.paid_by = user if getattr(user, 'is_authenticated', False) else None
        batch.paid_at = timezone.now()
        batch.save(update_fields=['status', 'payout_reference', 'evidence_url', 'evidence_file', 'paid_by', 'paid_at', 'updated_at'])
        SupplierPayableLedger.objects.filter(payout_batch_entry__batch=batch).update(
            status=SupplierPayableLedger.STATUS_PAID,
            payout_reference=reference,
        )
        batch.refresh_from_db()
    try:
        from apps.notifications.services import queue_supplier_payout_paid_email

        queue_supplier_payout_paid_email(batch)
    except Exception:
        pass
    _post_supplier_payout_accounting(batch, user=user)
    return batch


def _post_supplier_payable_accounting(ledger) -> None:
    try:
        from apps.accounting.services import post_supplier_payable

        post_supplier_payable(ledger)
    except Exception:
        logger.exception('Failed to post supplier payable accounting for %s', getattr(ledger, 'id', ''))


def _post_supplier_payout_accounting(batch, *, user=None) -> None:
    try:
        from apps.accounting.services import post_supplier_payout

        post_supplier_payout(batch, user=user)
    except Exception:
        logger.exception('Failed to post supplier payout accounting for %s', getattr(batch, 'batch_reference', ''))


def cancel_supplier_payout_batch(batch, *, user=None, reason=''):
    SupplierPayoutBatch = apps.get_model('marketplace', 'SupplierPayoutBatch')
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    if batch.status == SupplierPayoutBatch.STATUS_PAID:
        raise ValueError('Paid payout batches cannot be cancelled.')
    with transaction.atomic():
        batch.status = SupplierPayoutBatch.STATUS_CANCELLED
        if reason:
            batch.notes = f'{batch.notes}\nCancellation reason: {reason}'.strip()
        batch.save(update_fields=['status', 'notes', 'updated_at'])
        SupplierPayableLedger.objects.filter(payout_batch_entry__batch=batch, status=SupplierPayableLedger.STATUS_APPROVED).update(
            status=SupplierPayableLedger.STATUS_PAYABLE,
            payout_reference='',
        )
    return batch


def create_supplier_debit_adjustments_for_refund(refund_ledger, *, created_by=None):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    SupplierPayableAdjustment = apps.get_model('marketplace', 'SupplierPayableAdjustment')
    PaymentRefundLedger = apps.get_model('payments', 'PaymentRefundLedger')

    order = refund_ledger.order
    if not order:
        return []

    paid_payables = list(
        SupplierPayableLedger.objects.select_related('supplier', 'partner', 'order', 'line')
        .filter(order=order, status=SupplierPayableLedger.STATUS_PAID)
        .order_by('id')
    )
    if not paid_payables:
        return []

    order_total = _money(getattr(order, 'total_incl_tax', ZERO))
    refund_amount = _money(getattr(refund_ledger, 'amount', ZERO))
    if order_total <= ZERO or refund_amount <= ZERO:
        return []
    ratio = min(refund_amount / order_total, Decimal('1.00'))
    is_completed = refund_ledger.status == PaymentRefundLedger.STATUS_SUCCEEDED

    adjustments = []
    with transaction.atomic():
        for payable in paid_payables:
            adjustment_amount = min(_money(payable.payable_total), _money(_money(payable.payable_total) * ratio))
            if adjustment_amount <= ZERO:
                continue
            adjustment, _ = SupplierPayableAdjustment.objects.get_or_create(
                payable=payable,
                source_reference=refund_ledger.refund_reference,
                defaults={
                    'adjustment_reference': _next_adjustment_reference(SupplierPayableAdjustment),
                    'supplier': payable.supplier,
                    'partner': payable.partner,
                    'order': payable.order,
                    'line': payable.line,
                    'adjustment_type': SupplierPayableAdjustment.TYPE_DEBIT,
                    'status': SupplierPayableAdjustment.STATUS_APPLIED if is_completed else SupplierPayableAdjustment.STATUS_PENDING_REVIEW,
                    'amount': adjustment_amount,
                    'currency': payable.currency,
                    'reason': refund_ledger.reason or 'Customer refund after supplier payout.',
                    'metadata': {
                        'refund_ledger_id': refund_ledger.id,
                        'refund_reference': refund_ledger.refund_reference,
                        'refund_amount': str(refund_amount),
                        'order_total': str(order_total),
                        'proration_ratio': str(ratio),
                        'payable_id': payable.id,
                    },
                    'created_by': created_by if getattr(created_by, 'is_authenticated', False) else None,
                    'applied_by': created_by if is_completed and getattr(created_by, 'is_authenticated', False) else None,
                    'applied_at': timezone.now() if is_completed else None,
                },
            )
            if is_completed and adjustment.status != SupplierPayableAdjustment.STATUS_APPLIED:
                adjustment.status = SupplierPayableAdjustment.STATUS_APPLIED
                adjustment.applied_by = created_by if getattr(created_by, 'is_authenticated', False) else adjustment.applied_by
                adjustment.applied_at = adjustment.applied_at or timezone.now()
                adjustment.save(update_fields=['status', 'applied_by', 'applied_at', 'updated_at'])
            adjustments.append(adjustment)
    return adjustments


def mark_supplier_adjustments_applied_for_source(source_reference, *, user=None):
    SupplierPayableAdjustment = apps.get_model('marketplace', 'SupplierPayableAdjustment')
    reference = (source_reference or '').strip()
    if not reference:
        return []
    with transaction.atomic():
        adjustments = list(
            SupplierPayableAdjustment.objects.select_for_update().filter(
                source_reference=reference,
                status__in=[
                    SupplierPayableAdjustment.STATUS_PENDING_REVIEW,
                    SupplierPayableAdjustment.STATUS_APPROVED,
                ],
            )
        )
        for adjustment in adjustments:
            adjustment.status = SupplierPayableAdjustment.STATUS_APPLIED
            adjustment.applied_by = user if getattr(user, 'is_authenticated', False) else adjustment.applied_by
            adjustment.applied_at = adjustment.applied_at or timezone.now()
            adjustment.save(update_fields=['status', 'applied_by', 'applied_at', 'updated_at'])
    return adjustments


@transaction.atomic
def apply_supplier_return_to_payables(return_case, *, created_by=None):
    SupplierPayableLedger = apps.get_model('marketplace', 'SupplierPayableLedger')
    SupplierPayableAdjustment = apps.get_model('marketplace', 'SupplierPayableAdjustment')
    PaymentReturnCase = apps.get_model('payments', 'PaymentReturnCase')

    quantity = int(return_case.accepted_quantity or 0)
    if quantity <= 0:
        return []

    payables = list(
        SupplierPayableLedger.objects.select_for_update()
        .select_related('supplier', 'partner', 'order', 'line')
        .filter(order=return_case.order, line=return_case.line)
        .order_by('id')
    )
    adjustments = []
    is_refunded = return_case.status == PaymentReturnCase.STATUS_REFUNDED
    for payable in payables:
        return_cost = min(_money(payable.payable_total), _money(_money(payable.supplier_unit_cost) * Decimal(quantity)))
        if return_cost <= ZERO:
            continue

        if payable.status == SupplierPayableLedger.STATUS_PAID:
            adjustment, _ = SupplierPayableAdjustment.objects.get_or_create(
                payable=payable,
                source_reference=return_case.return_reference,
                defaults={
                    'adjustment_reference': _next_adjustment_reference(SupplierPayableAdjustment),
                    'supplier': payable.supplier,
                    'partner': payable.partner,
                    'order': payable.order,
                    'line': payable.line,
                    'adjustment_type': SupplierPayableAdjustment.TYPE_DEBIT,
                    'status': SupplierPayableAdjustment.STATUS_APPLIED if is_refunded else SupplierPayableAdjustment.STATUS_PENDING_REVIEW,
                    'amount': return_cost,
                    'currency': payable.currency,
                    'reason': return_case.reason or 'Accepted customer return after supplier payout.',
                    'metadata': {
                        'return_case_id': return_case.id,
                        'return_reference': return_case.return_reference,
                        'accepted_quantity': quantity,
                        'refund_amount': str(return_case.refund_amount),
                        'payable_id': payable.id,
                    },
                    'created_by': created_by if getattr(created_by, 'is_authenticated', False) else None,
                    'applied_by': created_by if is_refunded and getattr(created_by, 'is_authenticated', False) else None,
                    'applied_at': timezone.now() if is_refunded else None,
                },
            )
            if is_refunded and adjustment.status != SupplierPayableAdjustment.STATUS_APPLIED:
                adjustment.status = SupplierPayableAdjustment.STATUS_APPLIED
                adjustment.applied_by = created_by if getattr(created_by, 'is_authenticated', False) else adjustment.applied_by
                adjustment.applied_at = adjustment.applied_at or timezone.now()
                adjustment.save(update_fields=['status', 'applied_by', 'applied_at', 'updated_at'])
            adjustments.append(adjustment)
            continue

        if hasattr(payable, 'payout_batch_entry'):
            payable.status = SupplierPayableLedger.STATUS_ON_HOLD
            payable.source_status = 'return_after_batch'
            payable.reversal_reason = 'Return accepted after payout batch creation; review or cancel the payout batch.'
            metadata = payable.metadata or {}
            payable.metadata = {**metadata, 'return_hold_reference': return_case.return_reference, 'return_cost': str(return_cost)}
            payable.save(update_fields=['status', 'source_status', 'reversal_reason', 'metadata', 'updated_at'])
            continue

        if quantity >= int(payable.quantity or 0):
            payable.status = SupplierPayableLedger.STATUS_REVERSED
            payable.source_status = 'return_accepted'
            payable.reversal_reason = return_case.reason or 'Customer return accepted.'
        else:
            payable.quantity = max(0, int(payable.quantity or 0) - quantity)
            payable.payable_total = _money(payable.supplier_unit_cost * Decimal(payable.quantity))
            payable.source_status = 'partial_return_accepted'
            payable.reversal_reason = return_case.reason or 'Partial customer return accepted.'
        metadata = payable.metadata or {}
        adjustments_meta = metadata.get('return_adjustments') or []
        adjustments_meta.append(
            {
                'return_case_id': return_case.id,
                'return_reference': return_case.return_reference,
                'accepted_quantity': quantity,
                'return_cost': str(return_cost),
                'applied_at': timezone.now().isoformat(),
            }
        )
        payable.metadata = {**metadata, 'return_adjustments': adjustments_meta}
        payable.save(update_fields=['status', 'source_status', 'reversal_reason', 'quantity', 'payable_total', 'metadata', 'updated_at'])

    return adjustments


def _next_payout_reference(SupplierPayoutBatch):
    prefix = f'PO-{timezone.now():%Y%m%d}'
    count = SupplierPayoutBatch.objects.filter(batch_reference__startswith=prefix).count() + 1
    return f'{prefix}-{count:04d}'


def _next_adjustment_reference(SupplierPayableAdjustment):
    prefix = f'SA-{timezone.now():%Y%m%d}'
    count = SupplierPayableAdjustment.objects.filter(adjustment_reference__startswith=prefix).count() + 1
    return f'{prefix}-{count:04d}'
