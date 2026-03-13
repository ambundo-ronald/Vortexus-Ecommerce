import logging

from django.apps import apps
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.products import serialize_product_card
from apps.recommendations.services import RecommendationService

from .serializers import ProductListQuerySerializer, ProductWriteSerializer, QuoteRequestSerializer

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


def _build_product_detail(product) -> dict:
    card = serialize_product_card(product=product)
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
                "results": [serialize_product_card(product=item) for item in page_obj.object_list],
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
        return Response({"product": _build_product_detail(product)}, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(StaffWritePermissionMixin, APIView):
    recommendation_service = RecommendationService()

    def get(self, request, product_id: int):
        include_hidden = bool(request.user and request.user.is_staff)
        product = get_object_or_404(_product_queryset(include_hidden=include_hidden), id=product_id)
        detail = _build_product_detail(product)
        related = self.recommendation_service.recommend_for_product(product_id=product.id, limit=8)

        return Response({"product": detail, "related": related})

    def put(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        serializer = ProductWriteSerializer(instance=product, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product.id)
        return Response({"product": _build_product_detail(product)})

    def patch(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        serializer = ProductWriteSerializer(instance=product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product.id)
        return Response({"product": _build_product_detail(product)})

    def delete(self, request, product_id: int):
        product = get_object_or_404(_product_queryset(include_hidden=True), id=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuoteRequestAPIView(APIView):
    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        logger.info("Quote request received: %s", payload)
        return Response(
            {
                "detail": "Quote request received. Our team will contact you shortly.",
                "received": payload,
            },
            status=status.HTTP_201_CREATED,
        )
