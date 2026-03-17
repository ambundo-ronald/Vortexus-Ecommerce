from celery import shared_task
from django.apps import apps
from django.contrib.auth import get_user_model

from .services import (
    send_account_registration_email,
    send_order_confirmation_email,
    send_password_changed_email,
    send_quote_request_notifications,
    send_shipping_update_email,
)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_account_registration_email_task(self, user_id: int) -> bool:
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if not user:
        return False
    return send_account_registration_email(user, raise_on_failure=True)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_password_changed_email_task(self, user_id: int) -> bool:
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if not user:
        return False
    return send_password_changed_email(user, raise_on_failure=True)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_quote_request_notifications_task(self, payload: dict, product_id: int | None = None) -> dict:
    Product = apps.get_model('catalogue', 'Product')
    product = Product.objects.filter(id=product_id).first() if product_id else None
    return send_quote_request_notifications(payload, product=product, raise_on_failure=True)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_order_confirmation_email_task(self, order_number: str) -> bool:
    Order = apps.get_model('order', 'Order')
    order = Order.objects.filter(number=order_number).select_related('user').first()
    if not order:
        return False
    return send_order_confirmation_email(order, raise_on_failure=True)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_shipping_update_email_task(
    self,
    order_number: str,
    *,
    status_label: str,
    tracking_reference: str = '',
    note: str = '',
) -> bool:
    Order = apps.get_model('order', 'Order')
    order = Order.objects.filter(number=order_number).select_related('user').first()
    if not order:
        return False
    return send_shipping_update_email(
        order,
        status_label=status_label,
        tracking_reference=tracking_reference,
        note=note,
        raise_on_failure=True,
    )
