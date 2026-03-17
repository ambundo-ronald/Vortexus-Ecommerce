from apps.common.async_utils import dispatch_background_task

from .tasks import refresh_product_recommendations, refresh_trending_recommendations


def queue_trending_refresh(*, limit: int = 24) -> None:
    dispatch_background_task(refresh_trending_recommendations, run_kwargs={'limit': limit})


def queue_product_refresh(*, product_id: int, limit: int = 12) -> None:
    dispatch_background_task(refresh_product_recommendations, run_kwargs={'product_id': product_id, 'limit': limit})
