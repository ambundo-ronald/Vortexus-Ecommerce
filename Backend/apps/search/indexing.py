import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from apps.image_search.tasks import remove_product_image_embedding, sync_product_image_index

from .tasks import delete_product_from_search, index_product_for_search

logger = logging.getLogger(__name__)


def schedule_product_reindex(product_id: int, *, regenerate_image_embedding: bool = False, defer: bool = True) -> None:
    def runner():
        cache.clear()
        _dispatch(index_product_for_search, product_id=product_id)
        _dispatch(
            sync_product_image_index,
            product_id=product_id,
            regenerate_embedding=regenerate_image_embedding,
        )

    _maybe_on_commit(runner, defer=defer)


def schedule_product_delete(product_id: int, *, defer: bool = True) -> None:
    def runner():
        cache.clear()
        _dispatch(delete_product_from_search, product_id=product_id)
        _dispatch(remove_product_image_embedding, product_id=product_id)

    _maybe_on_commit(runner, defer=defer)


def _dispatch(task, **kwargs) -> None:
    if getattr(settings, 'ENABLE_ASYNC_TASKS', False):
        task.delay(**kwargs)
        return

    try:
        task.run(**kwargs)
    except Exception as exc:
        logger.warning('Could not execute %s for product %s: %s', task.name, kwargs.get('product_id'), exc)


def _maybe_on_commit(callback, *, defer: bool) -> None:
    connection = transaction.get_connection()
    if defer and connection.in_atomic_block:
        transaction.on_commit(callback)
        return
    callback()
