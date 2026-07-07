import logging

from oscar.apps.partner.exceptions import InvalidStockAdjustment

logger = logging.getLogger(__name__)


def _int_quantity(value) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _line_can_track_allocations(line) -> bool:
    try:
        return bool(getattr(line, 'can_track_allocations', False))
    except AttributeError:
        return False


def safe_cancel_line_allocation(line) -> int:
    quantity = _int_quantity(getattr(line, 'num_allocated', 0))
    if quantity <= 0 or not _line_can_track_allocations(line):
        return 0

    try:
        line.cancel_allocation(quantity)
        return quantity
    except InvalidStockAdjustment:
        logger.warning(
            'Could not cancel stale allocation for order line %s.',
            getattr(line, 'id', None),
            exc_info=True,
        )
        return 0


def safe_consume_line_allocation(line) -> int:
    quantity = _int_quantity(getattr(line, 'num_allocated', 0))
    if quantity <= 0 or not _line_can_track_allocations(line):
        return 0

    stockrecord = getattr(line, 'stockrecord', None)
    consumable_quantity = quantity
    if stockrecord and getattr(stockrecord, 'can_track_allocations', False):
        consumable_quantity = min(
            quantity,
            _int_quantity(getattr(stockrecord, 'num_allocated', 0)),
            _int_quantity(getattr(stockrecord, 'num_in_stock', 0)),
        )

    consumed = 0
    if consumable_quantity > 0:
        try:
            line.consume_allocation(consumable_quantity)
            consumed = consumable_quantity
        except InvalidStockAdjustment:
            logger.warning(
                'Could not consume allocation for order line %s; clearing stale allocation instead.',
                getattr(line, 'id', None),
                exc_info=True,
            )

    try:
        line.refresh_from_db(fields=['num_allocated', 'allocation_cancelled'])
    except Exception:
        line.refresh_from_db()

    remaining = _int_quantity(getattr(line, 'num_allocated', 0))
    if remaining > 0:
        safe_cancel_line_allocation(line)

    return consumed
