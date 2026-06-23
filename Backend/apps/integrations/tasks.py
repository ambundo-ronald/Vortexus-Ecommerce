from celery import shared_task

from .erpnext_sync import (
    ERPNextSyncService,
    export_order_to_active_erpnext,
    export_paid_order_accounting_to_active_erpnext,
    export_refund_credit_note_to_active_erpnext,
    sync_active_erpnext_stock,
    sync_customer_to_active_erpnext,
    sync_order_cancellation_to_active_erpnext,
)
from .models import IntegrationConnection


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3},
)
def sync_erpnext_connection_catalog(connection_id: int, include_stock: bool = True):
    connection = IntegrationConnection.objects.get(id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
    return ERPNextSyncService(connection).import_catalog(include_stock=include_stock)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3},
)
def sync_erpnext_connection_stock(connection_id: int):
    connection = IntegrationConnection.objects.get(id=connection_id, connection_type=IntegrationConnection.TYPE_ERPNEXT)
    return ERPNextSyncService(connection).sync_stock()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3},
)
def sync_all_active_erpnext_stock():
    return sync_active_erpnext_stock()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def export_order_to_erpnext(order_number: str):
    return export_order_to_active_erpnext(order_number)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def sync_customer_to_erpnext(user_id: int):
    return sync_customer_to_active_erpnext(user_id)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def export_paid_order_accounting_to_erpnext(payment_reference: str):
    return export_paid_order_accounting_to_active_erpnext(payment_reference)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def sync_order_cancellation_to_erpnext(order_number: str, reason: str = ''):
    return sync_order_cancellation_to_active_erpnext(order_number, reason=reason)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def export_refund_credit_note_to_erpnext(payment_reference: str, refund_amount: str = '', reason: str = '', refund_reference: str = ''):
    return export_refund_credit_note_to_active_erpnext(
        payment_reference,
        refund_amount=refund_amount,
        reason=reason,
        refund_reference=refund_reference,
    )
