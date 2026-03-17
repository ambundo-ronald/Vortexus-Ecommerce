import logging

from django.apps import apps
from django.conf import settings
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .indexing import schedule_product_delete, schedule_product_reindex

logger = logging.getLogger(__name__)

Product = apps.get_model('catalogue', 'Product')
StockRecord = apps.get_model('partner', 'StockRecord')
ProductImage = apps.get_model('catalogue', 'ProductImage')
ProductAttributeValue = apps.get_model('catalogue', 'ProductAttributeValue')


@receiver(post_save, sender=Product)
def product_saved_for_search(sender, instance, **kwargs) -> None:
    if not instance.is_public:
        schedule_product_delete(instance.id)
        return

    schedule_product_reindex(instance.id)


@receiver(post_delete, sender=Product)
def product_deleted_for_search(sender, instance, **kwargs) -> None:
    schedule_product_delete(instance.id)


@receiver(post_save, sender=StockRecord)
def stockrecord_saved_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id)


@receiver(post_delete, sender=StockRecord)
def stockrecord_deleted_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id)


@receiver(post_save, sender=ProductImage)
def product_image_saved_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id, regenerate_image_embedding=True)


@receiver(post_delete, sender=ProductImage)
def product_image_deleted_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id, regenerate_image_embedding=True)


@receiver(post_save, sender=ProductAttributeValue)
def product_attribute_saved_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id)


@receiver(post_delete, sender=ProductAttributeValue)
def product_attribute_deleted_for_search(sender, instance, **kwargs) -> None:
    if not instance.product_id:
        return
    schedule_product_reindex(instance.product_id)


@receiver(m2m_changed, sender=Product.categories.through)
def product_categories_changed_for_search(sender, instance, action, reverse, model, pk_set, **kwargs) -> None:
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return

    if reverse:
        if pk_set:
            product_ids = list(pk_set)
        else:
            product_ids = list(instance.products.values_list('id', flat=True))
        for product_id in product_ids:
            schedule_product_reindex(product_id)
        return

    schedule_product_reindex(instance.id)
