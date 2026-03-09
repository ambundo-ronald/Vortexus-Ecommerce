from celery import shared_task

from .services import RecommendationService


@shared_task
def refresh_trending_recommendations(limit: int = 24) -> int:
    service = RecommendationService()
    results = service.trending(limit=limit)
    return len(results)


@shared_task
def refresh_product_recommendations(product_id: int, limit: int = 12) -> int:
    service = RecommendationService()
    results = service.recommend_for_product(product_id=product_id, limit=limit)
    return len(results)
