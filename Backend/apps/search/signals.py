import logging

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.image_search.tasks import generate_product_image_embedding

from .tasks import index_product_for_search

logger = logging.getLogger(__name__)

Product = apps.get_model('catalogue', 'Product')


@receiver(post_save, sender=Product)
def product_saved_for_search(sender, instance, **kwargs) -> None:
    if not instance.is_public:
        return

    if not getattr(settings, 'ENABLE_ASYNC_TASKS', False):
        return

    for task, label in (
        (index_product_for_search, 'search-index'),
        (generate_product_image_embedding, 'image-embedding'),
    ):
        try:
            task.delay(instance.id)
        except Exception as exc:
            logger.warning('Could not enqueue %s task for product %s: %s', label, instance.id, exc)
