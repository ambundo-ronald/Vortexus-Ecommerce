from django.apps import apps
from django.db import transaction


class InventoryReservationError(Exception):
    pass


def _line_queryset():
    Line = apps.get_model('basket', 'Line')
    return Line.objects.select_related('basket', 'stockrecord__product__product_class', 'product')


def _stockrecord_queryset():
    StockRecord = apps.get_model('partner', 'StockRecord')
    return StockRecord.objects.all()


def _reservation_queryset():
    StockReservation = apps.get_model('inventory', 'StockReservation')
    return StockReservation.objects.select_related('basket', 'line', 'stockrecord__product__product_class')


def _can_track_stock(stockrecord) -> bool:
    return bool(stockrecord and stockrecord.product.get_product_class().track_stock)


def _available_for_line(stockrecord, reserved_quantity: int) -> int:
    net_stock = int(getattr(stockrecord, 'net_stock_level', 0) or 0)
    return max(net_stock + reserved_quantity, 0)


def _reservation_message(product_title: str, requested: int, available: int) -> str:
    return (
        f'Only {available} unit(s) of "{product_title}" are currently available for checkout. '
        f'Requested quantity: {requested}.'
    )


@transaction.atomic
def sync_basket_line_reservation(line, desired_quantity: int | None = None):
    line = _line_queryset().get(pk=line.pk)
    reservation = _reservation_queryset().filter(line=line).first()
    stockrecord = line.stockrecord

    if desired_quantity is None:
        desired_quantity = int(line.quantity)
    desired_quantity = max(int(desired_quantity), 0)

    if reservation and (reservation.stockrecord_id != line.stockrecord_id or not _can_track_stock(stockrecord)):
        locked_stockrecord = _stockrecord_queryset().select_for_update().get(pk=reservation.stockrecord_id)
        if _can_track_stock(locked_stockrecord) and reservation.quantity:
            locked_stockrecord.cancel_allocation(reservation.quantity)
        reservation.delete()
        reservation = None

    if not _can_track_stock(stockrecord):
        return None

    locked_stockrecord = _stockrecord_queryset().select_for_update().get(pk=stockrecord.pk)
    reserved_quantity = reservation.quantity if reservation else 0
    available_quantity = _available_for_line(locked_stockrecord, reserved_quantity)
    if desired_quantity > available_quantity:
        raise InventoryReservationError(
            _reservation_message(line.product.get_title(), desired_quantity, available_quantity)
        )

    delta = desired_quantity - reserved_quantity
    if delta > 0:
        locked_stockrecord.allocate(delta)
    elif delta < 0:
        locked_stockrecord.cancel_allocation(-delta)

    if desired_quantity == 0:
        if reservation:
            reservation.delete()
        return None

    StockReservation = apps.get_model('inventory', 'StockReservation')
    if reservation:
        if reservation.quantity != desired_quantity:
            reservation.quantity = desired_quantity
            reservation.save(update_fields=['quantity', 'updated_at'])
        return reservation

    return StockReservation.objects.create(
        basket=line.basket,
        line=line,
        stockrecord=locked_stockrecord,
        quantity=desired_quantity,
    )


@transaction.atomic
def release_basket_line_reservation(line):
    reservation = _reservation_queryset().filter(line_id=line.id).first()
    if not reservation:
        return False

    locked_stockrecord = _stockrecord_queryset().select_for_update().get(pk=reservation.stockrecord_id)
    if _can_track_stock(locked_stockrecord) and reservation.quantity:
        locked_stockrecord.cancel_allocation(reservation.quantity)
    reservation.delete()
    return True


@transaction.atomic
def prepare_basket_for_order_submission(basket):
    lines = list(
        _line_queryset()
        .filter(basket=basket)
        .exclude(stockrecord=None)
        .order_by('stockrecord_id', 'id')
    )
    reservations = {
        reservation.line_id: reservation
        for reservation in _reservation_queryset().filter(basket=basket).order_by('stockrecord_id', 'id')
    }

    stockrecord_ids = sorted(
        {
            line.stockrecord_id
            for line in lines
            if _can_track_stock(line.stockrecord)
        }
    )
    locked_stockrecords = {
        stockrecord.id: stockrecord
        for stockrecord in _stockrecord_queryset().select_for_update().filter(id__in=stockrecord_ids)
    }

    for line in lines:
        if not _can_track_stock(line.stockrecord):
            continue
        reservation = reservations.get(line.id)
        reserved_quantity = reservation.quantity if reservation else 0
        locked_stockrecord = locked_stockrecords[line.stockrecord_id]
        available_quantity = _available_for_line(locked_stockrecord, reserved_quantity)
        if line.quantity > available_quantity:
            raise InventoryReservationError(
                _reservation_message(line.product.get_title(), line.quantity, available_quantity)
            )

    for reservation in reservations.values():
        locked_stockrecord = locked_stockrecords.get(reservation.stockrecord_id)
        if locked_stockrecord and reservation.quantity:
            locked_stockrecord.cancel_allocation(reservation.quantity)
        reservation.delete()

    return True


def reserved_quantity_for_line(line) -> int:
    reservation = getattr(line, 'stock_reservation', None)
    if reservation is None:
        return 0
    return int(reservation.quantity or 0)


def available_quantity_for_line(line) -> int | None:
    stockrecord = getattr(line, 'stockrecord', None)
    if not stockrecord:
        return None
    return _available_for_line(stockrecord, reserved_quantity_for_line(line))
