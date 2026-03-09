from typing import Any

from django.apps import apps
from django.core.cache import cache
from django.db.models import Count

from apps.common.products import serialize_product_card


class RecommendationService:
    def recommend(self, product_id: int | None = None, user_id: int | None = None, limit: int = 12) -> dict[str, Any]:
        if product_id:
            return {
                'results': self.recommend_for_product(product_id=product_id, limit=limit),
                'strategy': 'similar-products',
            }

        if user_id:
            return {
                'results': self.recommend_for_user(user_id=user_id, limit=limit),
                'strategy': 'user-history',
            }

        return {
            'results': self.trending(limit=limit),
            'strategy': 'trending',
        }

    def recommend_for_product(self, product_id: int, limit: int) -> list[dict[str, Any]]:
        cache_key = f'recommendations:product:{product_id}:{limit}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        Product = apps.get_model('catalogue', 'Product')
        product = Product.objects.filter(id=product_id, is_public=True).prefetch_related('categories').first()
        if not product:
            return []

        category_ids = list(product.categories.values_list('id', flat=True))

        queryset = (
            Product.objects.filter(is_public=True, categories__id__in=category_ids)
            .exclude(id=product.id)
            .prefetch_related('stockrecords')
            .distinct()
            .order_by('-date_updated')
        )

        results = [serialize_product_card(product=item, reason='similar-category') for item in queryset[:limit]]
        cache.set(cache_key, results, timeout=60 * 30)
        return results

    def recommend_for_user(self, user_id: int, limit: int) -> list[dict[str, Any]]:
        OrderLine = apps.get_model('order', 'Line')
        user_product_ids = list(
            OrderLine.objects.filter(order__user_id=user_id).values_list('product_id', flat=True).distinct()[:100]
        )

        if not user_product_ids:
            return self.trending(limit=limit)

        Product = apps.get_model('catalogue', 'Product')
        queryset = (
            Product.objects.filter(is_public=True, id__in=user_product_ids)
            .prefetch_related('stockrecords')
            .order_by('-date_updated')
        )

        results = [serialize_product_card(product=item, reason='history-based') for item in queryset[:limit]]
        if len(results) < limit:
            seen_ids = {item['id'] for item in results}
            for candidate in self.trending(limit=limit * 2):
                if candidate['id'] in seen_ids:
                    continue
                results.append(candidate)
                if len(results) >= limit:
                    break

        return results

    def trending(self, limit: int) -> list[dict[str, Any]]:
        cache_key = f'recommendations:trending:{limit}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        Product = apps.get_model('catalogue', 'Product')
        OrderLine = apps.get_model('order', 'Line')

        trending_ids = list(
            OrderLine.objects.values('product_id')
            .annotate(total=Count('id'))
            .order_by('-total')
            .values_list('product_id', flat=True)[: max(limit * 2, 24)]
        )

        queryset = Product.objects.filter(is_public=True).prefetch_related('stockrecords')
        if trending_ids:
            queryset = queryset.filter(id__in=trending_ids)

        results = [serialize_product_card(product=item, reason='trending') for item in queryset[:limit]]
        cache.set(cache_key, results, timeout=60 * 15)
        return results
