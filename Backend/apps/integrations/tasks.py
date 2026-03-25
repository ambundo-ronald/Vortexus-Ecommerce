from celery import shared_task

from .erpnext_sync import ERPNextSyncService, sync_active_erpnext_stock
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
