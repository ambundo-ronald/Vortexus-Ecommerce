import logging

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.common.currency import resolve_display_currency
from apps.common.products import serialize_product_card
from apps.notifications.services import queue_quote_request_notifications
from apps.recommendations.services import RecommendationService

from .serializers import ProductImageUploadSerializer, ProductListQuerySerializer, ProductWriteSerializer, QuoteRequestSerializer

logger = logging.getLogger(__name__)


def _serialize_category(category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "url": category.get_absolute_url(),
    }


def _get_primary_image_url(product) -> str:
    try:
        primary = product.primary_image()
    except TypeError:
        primary = product.primary_image
    except Exception:
        primary = None

    if primary and getattr(primary, "original", None):
        return primary.original.url or ""
    return ""


def _product_queryset(include_hidden: bool = False):
    Product = apps.get_model("catalogue", "Product")
    queryset = (
        Product.objects.exclude(structure="parent")
        .prefetch_related("stockrecords", "categories", "attribute_values__attribute", "images")
        .distinct()
    )
    if include_hidden:
        return queryset
    return queryset.filter(is_public=True)


def _build_product_detail(product, display_currency: str | None = None) -> dict:
    card = serialize_product_card(product=product, display_currency=display_currency)
    specs = []
    for attribute_value in product.attribute_values.all():
        attribute = getattr(attribute_value, "attribute", None)
        if not attribute:
            continue
        value = str(attribute_value.value) if getattr(attribute_value, "value", None) not in (None, "") else ""
        if not value:
            value = str(attribute_value)
        specs.append(
            {
                "name": attribute.name,
                "code": attribute.code,
                "value": value,
            }
        )

    images = []
    for image in product.images.all():
        if getattr(image, "original", None):
            images.append(image.original.url or "")

    return {
        **card,
        "description": product.description or "",
        "images": images,
        "primary_image": _get_primary_image_url(product),
        "categories": [_serialize_category(category) for category in product.categories.all()],
        "specifications": specs,
        "updated_at": product.date_updated,
        "is_public": product.is_public,
    }


def _serialize_product_image(image, fallback_alt: str = '') -> dict:
    alt = (getattr(image, 'caption', '') or fallback_alt or '').strip()
    src = ''
    if getattr(image, 'original', None):
        src = image.original.url or ''
    return {
        'id': image.id,
        'src': src,
        'alt': alt,
        'displayOrder': getattr(image, 'display_order', 0),
    }


def _stockrecord_for_product(product):
    return product.stockrecords.first() if hasattr(product, 'stockrecords') else None


def _attribute_value_map(product) -> dict[str, str]:
    values: dict[str, str] = {}
    for attribute_value in product.attribute_values.all():
        attribute = getattr(attribute_value, 'attribute', None)
        if not attribute:
            continue
        raw_value = getattr(attribute_value, 'value', None)
        if raw_value in (None, ''):
            raw_value = str(attribute_value)
        values[attribute.code] = str(raw_value)
    return values


def _serialize_admin_product_row(product, display_currency: str | None = None) -> dict:
    card = serialize_product_card(product=product, display_currency=display_currency)
    stockrecord = _stockrecord_for_product(product)
    category = product.categories.first()
    return {
        'id': product.id,
        'name': product.title,
        'sku': product.upc,
        'price': card.get('price'),
        'currency': card.get('currency'),
        'status': 'Active' if product.is_public else 'Draft',
        'category': category.name if category else 'Uncategorized',
        'categorySlug': category.slug if category else '',
        'stock': int(getattr(stockrecord, 'num_in_stock', 0) or 0),
        'imageUrl': card.get('thumbnail', ''),
        'isPublic': product.is_public,
        'updatedAt': product.date_updated,
    }


def _build_admin_product_detail(product, display_currency: str | None = None) -> dict:
    detail = _build_product_detail(product=product, display_currency=display_currency)
    stockrecord = _stockrecord_for_product(product)
    attributes = _attribute_value_map(product)
    return {
        'id': product.id,
        'name': product.title,
        'sku': product.upc,
        'price': detail.get('price'),
        'currency': detail.get('currency'),
        'status': 'active' if product.is_public else 'draft',
        'stock': int(getattr(stockrecord, 'num_in_stock', 0) or 0),
        'description': product.description or '',
        'imageUrl': detail.get('primary_image', ''),
        'images': [_serialize_product_image(image, fallback_alt=product.title) for image in product.images.all()],
        'category': str(detail['categories'][0]['id']) if detail.get('categories') else '',
        'categoryIds': [category['id'] for category in detail.get('categories', [])],
        'categories': detail.get('categories', []),
        'brand': attributes.get('brand', ''),
        'tags': attributes.get('tags', ''),
        'dimensions': attributes.get('dimensions', ''),
        'weight': float(attributes['weight_grams']) if attributes.get('weight_grams') not in (None, '') and str(attributes.get('weight_grams')).replace('.', '', 1).isdigit() else None,
        'chargeTax': True,
        'specifications': detail.get('specifications', []),
        'updatedAt': detail.get('updated_at'),
        'isPublic': product.is_public,
    }


class StaffWritePermissionMixin:
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class CategoryListAPIView(APIView):
    def get(self, request):
        Category = apps.get_model("catalogue", "Category")

        root_categories = Category.objects.filter(depth=1).order_by("name")
        results = []

        for root in root_categories:
            children = list(root.get_children().order_by("name")[:24])
            results.append(
                {
                    **_serialize_category(root),
                    "children_count": len(children),
                    "children": [_serialize_category(child) for child in children],
                }
            )

        return Response({"results": results})


class ProductListAPIView(StaffWritePermissionMixin, APIView):
    def get(self, request):
        serializer = ProductListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        display_currency = resolve_display_currency(request)

        Product = apps.get_model("catalogue", "Product")
        queryset = (
            Product.objects.filter(is_public=True)
            .exclude(structure="parent")
            .prefetch_related("stockrecords", "images", "categories")
            .annotate(list_price=Min("stockrecords__price"))
            .distinct()
        )

        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(upc__icontains=query) | Q(description__icontains=query)
            )

        category = params.get("category")
        if category:
            queryset = queryset.filter(categories__slug=category)

        in_stock = params.get("in_stock")
        if in_stock is True:
            queryset = queryset.filter(stockrecords__num_in_stock__gt=0)

        min_price = params.get("min_price")
        if min_price is not None:
            queryset = queryset.filter(list_price__gte=min_price)

        max_price = params.get("max_price")
        if max_price is not None:
            queryset = queryset.filter(list_price__lte=max_price)

        sort_by = params.get("sort_by", "relevance")
        if sort_by == "newest":
            queryset = queryset.order_by("-date_updated", "title")
        elif sort_by == "price_asc":
            queryset = queryset.order_by("list_price", "title")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-list_price", "title")
        elif sort_by == "title_asc":
            queryset = queryset.order_by("title")
        else:
            queryset = queryset.order_by("title")

        page = params.get("page", 1)
        page_size = params.get("page_size", 24)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return Response(
            {
                "results": [
                    serialize_product_card(product=item, display_currency=display_currency)
                    for item in page_obj.object_list
                ],
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total": paginator.count,
                    "num_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                },
                "filters": {
                    "q": query,
                    "category": category,
                    "in_stock": in_stock,
                    "min_price": min_price,
                    "max_price": max_price,
                    "sort_by": sort_by,
                },
            }
        )

    def post(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product.id)
        display_currency = resolve_display_currency(request)
        record_audit_event(
            event_type='catalog.product_created',
            request=request,
            target=product,
            message='Catalog product created by staff.',
            metadata={'upc': product.upc, 'title': product.title},
        )
        return Response({"product": _build_product_detail(product, display_currency=display_currency)}, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(StaffWritePermissionMixin, APIView):
    recommendation_service = RecommendationService()

    def get(self, request, product_id: int):
        include_hidden = bool(request.user and request.user.is_staff)
        display_currency = resolve_display_currency(request)
        product = get_object_or_404(_product_queryset(include_hidden=include_hidden), id=product_id)
        detail = _build_product_detail(product, display_currency=display_currency)
        related = self.recommendation_service.recommend_for_product(
            product_id=product.id,
            limit=8,
            display_currency=display_currency,
        )

        return Response({"product": detail, "related": related})

    def put(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        previous_title = product.title
        serializer = ProductWriteSerializer(instance=product, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product.id)
        display_currency = resolve_display_currency(request)
        record_audit_event(
            event_type='catalog.product_updated',
            request=request,
            target=product,
            message='Catalog product fully updated by staff.',
            metadata={'previous_title': previous_title, 'current_title': product.title, 'update_mode': 'put'},
        )
        return Response({"product": _build_product_detail(product, display_currency=display_currency)})

    def patch(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        previous_title = product.title
        serializer = ProductWriteSerializer(instance=product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product.id)
        display_currency = resolve_display_currency(request)
        record_audit_event(
            event_type='catalog.product_updated',
            request=request,
            target=product,
            message='Catalog product partially updated by staff.',
            metadata={'previous_title': previous_title, 'current_title': product.title, 'update_mode': 'patch'},
        )
        return Response({"product": _build_product_detail(product, display_currency=display_currency)})

    def delete(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        metadata = {'upc': product.upc, 'title': product.title}
        product.delete()
        record_audit_event(
            event_type='catalog.product_deleted',
            request=request,
            message='Catalog product deleted by staff.',
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        serializer = ProductListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        display_currency = resolve_display_currency(request)

        queryset = (
            _product_queryset(include_hidden=True)
            .annotate(list_price=Min('stockrecords__price'))
            .order_by('title')
        )

        query = params.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(upc__icontains=query) | Q(description__icontains=query)
            )

        category = params.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)

        in_stock = params.get('in_stock')
        if in_stock is True:
            queryset = queryset.filter(stockrecords__num_in_stock__gt=0)

        min_price = params.get('min_price')
        if min_price is not None:
            queryset = queryset.filter(list_price__gte=min_price)

        max_price = params.get('max_price')
        if max_price is not None:
            queryset = queryset.filter(list_price__lte=max_price)

        sort_by = params.get('sort_by', 'relevance')
        if sort_by == 'newest':
            queryset = queryset.order_by('-date_updated', 'title')
        elif sort_by == 'price_asc':
            queryset = queryset.order_by('list_price', 'title')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-list_price', 'title')
        else:
            queryset = queryset.order_by('title')

        page = params.get('page', 1)
        page_size = params.get('page_size', 24)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return Response(
            {
                'results': [
                    _serialize_admin_product_row(product=item, display_currency=display_currency)
                    for item in page_obj.object_list
                ],
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class AdminProductDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        display_currency = resolve_display_currency(request)
        return Response({'product': _build_admin_product_detail(product, display_currency=display_currency)})


class AdminProductImageCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, product_id: int):
        ProductImage = apps.get_model('catalogue', 'ProductImage')

        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        serializer = ProductImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['image']
        alt = (serializer.validated_data.get('alt') or product.title or '').strip()
        filename_root = slugify(product.title or product.upc or f'product-{product.id}') or f'product-{product.id}'
        upload_name = getattr(uploaded_file, 'name', '') or f'{filename_root}.webp'
        final_name = upload_name if '.' in upload_name else f'{filename_root}.webp'

        product_image = ProductImage(
            product=product,
            caption=alt,
            display_order=product.images.count(),
        )
        product_image.original.save(final_name, ContentFile(uploaded_file.read()), save=False)
        product_image.save()

        record_audit_event(
            event_type='catalog.product_image_uploaded',
            request=request,
            target=product,
            message='Catalog product image uploaded by staff.',
            metadata={'image_id': product_image.id, 'product_id': product.id, 'filename': final_name},
        )

        return Response({'image': _serialize_product_image(product_image, fallback_alt=product.title)}, status=status.HTTP_201_CREATED)


class AdminProductImageDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, product_id: int, image_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        image = get_object_or_404(product.images.all(), id=image_id)
        metadata = {
            'image_id': image.id,
            'product_id': product.id,
            'filename': getattr(getattr(image, 'original', None), 'name', ''),
        }
        image.delete()
        record_audit_event(
            event_type='catalog.product_image_deleted',
            request=request,
            target=product,
            message='Catalog product image deleted by staff.',
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteRequestAPIView(APIView):
    throttle_scope = 'quote_request'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        product = None

        product_id = payload.get('product_id')
        if product_id:
            product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)

        logger.info("Quote request received: %s", payload)
        queue_quote_request_notifications(payload, product=product)
        record_audit_event(
            event_type='quotes.requested',
            request=request,
            target=product,
            message='Quote request submitted.',
            metadata={
                'email': payload.get('email', ''),
                'company': payload.get('company', ''),
                'product_id': product.id if product else None,
            },
        )
        return Response(
            {
                "detail": "Quote request received. Our team will contact you shortly.",
                "received": payload,
                "notifications": {"queued": True},
            },
            status=status.HTTP_201_CREATED,
        )
