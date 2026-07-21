from __future__ import annotations

import logging
from html import escape

from django.apps import apps
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.views import View

from apps.common.catalog import brand_slug, product_brand


logger = logging.getLogger(__name__)


class RobotsTxtView(View):
    def get(self, request):
        base_url = settings.STOREFRONT_BASE_URL.rstrip('/')
        lines = [
            'User-agent: *',
            'Allow: /',
            'Disallow: /account',
            'Disallow: /checkout',
            'Disallow: /login',
            'Disallow: /orders/track',
            'Disallow: /product-alerts',
            'Disallow: /quote',
            'Disallow: /register',
            'Disallow: /forgot-password',
            'Disallow: /reset-password',
            'Disallow: /search',
            'Disallow: /supplier',
            'Disallow: /unauthorized',
            'Disallow: /wishlists/shared',
            '',
            f'Sitemap: {base_url}/sitemap.xml',
            '',
        ]
        return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


class StorefrontSitemapView(View):
    def get(self, request):
        urls = [
            sitemap_url('/'),
            sitemap_url('/catalog'),
            sitemap_url('/offers'),
        ]
        try:
            urls.extend(category_urls())
            urls.extend(brand_urls())
            urls.extend(product_urls())
            urls.extend(offer_urls())
            urls.extend(range_urls())
        except Exception:
            logger.exception('Could not build dynamic storefront sitemap entries.')

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
            *urls,
            '</urlset>',
        ]
        return HttpResponse('\n'.join(xml), content_type='application/xml; charset=utf-8')


class ProductCanonicalRedirectView(View):
    def get(self, request, product_id: int):
        Product = apps.get_model('catalogue', 'Product')
        try:
            product = (
                Product.objects
                .filter(is_public=True)
                .exclude(structure='parent')
                .prefetch_related('categories', 'attribute_values__attribute')
                .get(id=product_id)
            )
        except Product.DoesNotExist as exc:
            raise Http404('Product not found') from exc

        canonical_url = f"{settings.STOREFRONT_BASE_URL.rstrip('/')}{product_canonical_path(product)}"
        return HttpResponsePermanentRedirect(canonical_url)


def category_urls() -> list[str]:
    Category = apps.get_model('catalogue', 'Category')
    return [
        sitemap_url(f'/catalog/category/{category.slug}', lastmod=getattr(category, 'date_updated', None))
        for category in Category.objects.filter(is_public=True).exclude(slug='').order_by('path')
    ]


def brand_urls() -> list[str]:
    Product = apps.get_model('catalogue', 'Product')
    brands: set[str] = set()
    for product in Product.objects.filter(is_public=True).exclude(structure='parent').prefetch_related('attribute_values__attribute'):
        brand = product_brand(product)
        slug = brand_slug(brand)
        if slug:
            brands.add(slug)
    return [sitemap_url(f'/catalog/brand/{slug}') for slug in sorted(brands)]


def product_urls() -> list[str]:
    Product = apps.get_model('catalogue', 'Product')
    products = (
        Product.objects
        .filter(is_public=True)
        .exclude(structure='parent')
        .prefetch_related('categories', 'attribute_values__attribute', 'images')
        .order_by('id')
    )
    return [
        sitemap_url(
            product_canonical_path(product),
            lastmod=getattr(product, 'date_updated', None),
            images=product_image_sitemap_entries(product),
        )
        for product in products
    ]


def offer_urls() -> list[str]:
    try:
        ConditionalOffer = apps.get_model('offer', 'ConditionalOffer')
    except LookupError:
        return []

    now = timezone.now()
    offers = (
        ConditionalOffer.objects
        .filter(status='Open')
        .exclude(slug='')
        .filter(Q(start_datetime__isnull=True) | Q(start_datetime__lte=now))
        .filter(Q(end_datetime__isnull=True) | Q(end_datetime__gte=now))
    )
    return [
        sitemap_url(f'/offers/{offer.slug}', lastmod=getattr(offer, 'date_updated', None))
        for offer in offers.distinct().order_by('slug')
    ]


def range_urls() -> list[str]:
    try:
        Range = apps.get_model('offer', 'Range')
    except LookupError:
        return []

    ranges = Range.objects.filter(is_public=True).exclude(slug='').order_by('slug')
    return [
        sitemap_url(f'/catalog/ranges/{range_obj.slug}', lastmod=getattr(range_obj, 'date_updated', None))
        for range_obj in ranges
    ]


def product_canonical_path(product) -> str:
    categories = list(product.categories.all())
    category = categories[0] if categories else None
    category_segments = [item.slug for item in category_path(category)] if category else []
    brand = brand_slug(product_brand(product))
    product_slug = product.slug or str(product.id)
    segments = [*category_segments, brand, product_slug]
    clean_segments = [slugify_segment(segment) for segment in segments if slugify_segment(segment)]
    return f"/products/{'/'.join(clean_segments or [str(product.id)])}"


def category_path(category) -> list:
    if not category:
        return []

    ancestors = []
    get_ancestors = getattr(category, 'get_ancestors', None)
    if callable(get_ancestors):
        try:
            ancestors = list(get_ancestors())
        except Exception:
            ancestors = []
    return [*ancestors, category]


def sitemap_url(path: str, lastmod=None, images: list[dict[str, str]] | None = None) -> str:
    loc = f"{settings.STOREFRONT_BASE_URL.rstrip('/')}{path if path.startswith('/') else f'/{path}'}"
    parts = [
        '  <url>',
        f'    <loc>{escape(loc)}</loc>',
    ]
    if lastmod:
        parts.append(f'    <lastmod>{lastmod.date().isoformat() if hasattr(lastmod, "date") else escape(str(lastmod))}</lastmod>')
    for image in images or []:
        image_loc = image.get('loc', '')
        if not image_loc:
            continue
        parts.extend([
            '    <image:image>',
            f'      <image:loc>{escape(image_loc)}</image:loc>',
        ])
        title = image.get('title', '')
        caption = image.get('caption', '')
        if title:
            parts.append(f'      <image:title>{escape(title)}</image:title>')
        if caption:
            parts.append(f'      <image:caption>{escape(caption)}</image:caption>')
        parts.append('    </image:image>')
    parts.append('  </url>')
    return '\n'.join(parts)


def product_image_sitemap_entries(product) -> list[dict[str, str]]:
    entries = []
    seen = set()
    for image in list(getattr(product, 'images', []).all() if hasattr(product, 'images') else []):
        original = getattr(image, 'original', None)
        url = absolute_media_url(getattr(original, 'url', '') if original else '')
        if not url or url in seen:
            continue
        seen.add(url)
        caption = (getattr(image, 'caption', '') or product.title or '').strip()
        entries.append({
            'loc': url,
            'title': product.title or '',
            'caption': caption,
        })
    return entries[:10]


def absolute_media_url(url: str) -> str:
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    base_url = getattr(settings, 'BACKEND_PUBLIC_BASE_URL', '') or getattr(settings, 'STOREFRONT_BASE_URL', '')
    return f"{base_url.rstrip('/')}{url if url.startswith('/') else f'/{url}'}"


def slugify_segment(value: str) -> str:
    return slugify(str(value or '').replace('&', ' and '))
