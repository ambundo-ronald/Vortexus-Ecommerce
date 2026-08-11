from celery import shared_task

from .erpnext_sync import (
    ERPNextSyncService,
    export_order_to_active_erpnext,
    export_paid_order_accounting_to_active_erpnext,
    export_refund_credit_note_to_active_erpnext,
    export_supplier_payout_batch_to_active_erpnext,
    sync_active_erpnext_stock,
    sync_customer_to_active_erpnext,
    sync_order_cancellation_to_active_erpnext,
)
from .google_merchant import (
    delete_product_from_active_google_merchant_connections,
    refresh_all_google_merchant_products,
    sync_product_to_active_google_merchant_connections,
)
from .google_merchant_sheets import sync_google_merchant_sheet
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


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def export_supplier_payout_batch_to_erpnext(batch_id: int):
    return export_supplier_payout_batch_to_active_erpnext(batch_id)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def sync_product_to_google_merchant(product_id: int):
    return sync_product_to_active_google_merchant_connections(product_id)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def delete_product_from_google_merchant(product_id: int, offer_id: str = ''):
    return delete_product_from_active_google_merchant_connections(product_id, offer_id=offer_id)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3},
)
def refresh_google_merchant_products():
    return refresh_all_google_merchant_products()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3},
)
def refresh_google_merchant_sheet():
    return sync_google_merchant_sheet()
