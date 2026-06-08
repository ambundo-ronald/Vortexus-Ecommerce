from django.apps import apps
from django.db.models import Q
from django.utils.text import slugify


def category_ids_for_slug(slug: str | None) -> list[int]:
    normalized = (slug or '').strip()
    if not normalized:
        return []

    Category = apps.get_model('catalogue', 'Category')
    category = Category.objects.filter(slug=normalized, is_public=True).first()
    if not category:
        return []

    ids = [category.id]
    try:
        ids.extend(category.get_descendants().filter(is_public=True).values_list('id', flat=True))
    except Exception:
        path = getattr(category, 'path', '')
        if path:
            ids.extend(
                Category.objects.filter(path__startswith=path, is_public=True)
                .exclude(id=category.id)
                .values_list('id', flat=True)
            )
    return list(dict.fromkeys(ids))


def filter_queryset_by_category_slug(queryset, slug: str | None):
    category_ids = category_ids_for_slug(slug)
    if not (slug or '').strip():
        return queryset
    if not category_ids:
        return queryset.none()
    return queryset.filter(categories__id__in=category_ids, categories__is_public=True)


def normalize_brand(value: str | None) -> str:
    return (value or '').strip()


def brand_slug(value: str | None) -> str:
    return slugify(normalize_brand(value))


def product_brand(product) -> str:
    for attribute_value in product.attribute_values.all():
        attribute = getattr(attribute_value, 'attribute', None)
        if not attribute or attribute.code != 'brand':
            continue
        value = (getattr(attribute_value, 'value_as_text', '') or '').strip()
        if value:
            return value
    return ''


def filter_queryset_by_brand(queryset, brand: str | None):
    normalized = normalize_brand(brand)
    if not normalized:
        return queryset

    return queryset.filter(
        attribute_values__attribute__code='brand'
    ).filter(
        Q(attribute_values__value_text__iexact=normalized)
        | Q(attribute_values__value_text__iexact=normalized.replace('-', ' '))
    )
