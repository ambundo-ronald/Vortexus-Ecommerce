from django.core.cache import cache
from django.db import transaction

from apps.common.async_utils import dispatch_background_task
from apps.image_search.tasks import remove_product_image_embedding, sync_product_image_index
from apps.recommendations.tasks import refresh_product_recommendations, refresh_trending_recommendations

from .tasks import delete_product_from_search, index_product_for_search


def schedule_product_reindex(product_id: int, *, regenerate_image_embedding: bool = False, defer: bool = True) -> None:
    def runner():
        cache.clear()
        dispatch_background_task(index_product_for_search, defer=False, run_kwargs={'product_id': product_id})
        dispatch_background_task(
            sync_product_image_index,
            defer=False,
            run_kwargs={
                'product_id': product_id,
                'regenerate_embedding': regenerate_image_embedding,
            },
        )
        dispatch_background_task(
            refresh_product_recommendations,
            defer=False,
            run_kwargs={'product_id': product_id, 'limit': 12},
        )
        dispatch_background_task(
            refresh_trending_recommendations,
            defer=False,
            run_kwargs={'limit': 24},
        )

    _maybe_on_commit(runner, defer=defer)


def schedule_product_delete(product_id: int, *, defer: bool = True) -> None:
    def runner():
        cache.clear()
        dispatch_background_task(delete_product_from_search, defer=False, run_kwargs={'product_id': product_id})
        dispatch_background_task(remove_product_image_embedding, defer=False, run_kwargs={'product_id': product_id})
        dispatch_background_task(
            refresh_trending_recommendations,
            defer=False,
            run_kwargs={'limit': 24},
        )

    _maybe_on_commit(runner, defer=defer)


def _maybe_on_commit(callback, *, defer: bool) -> None:
    connection = transaction.get_connection()
    if defer and connection.in_atomic_block:
        transaction.on_commit(callback)
        return
    callback()
