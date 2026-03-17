from django.apps import apps
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .supplier_serializers import (
    SupplierAdminStatusSerializer,
    SupplierDashboardSerializer,
    SupplierProductListSerializer,
    SupplierProductWriteSerializer,
    SupplierProfileSerializer,
    SupplierProfileWriteSerializer,
)
from .views import _build_product_detail


class SupplierOnlyPermission(permissions.BasePermission):
    message = 'Supplier access is required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'supplier_profile'))


class ApprovedSupplierWritePermission(SupplierOnlyPermission):
    message = 'An approved supplier profile is required for this action.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.supplier_profile.is_active_supplier


def _supplier_product_queryset(supplier_profile):
    Product = apps.get_model('catalogue', 'Product')
    return (
        Product.objects.exclude(structure='parent')
        .filter(stockrecords__partner=supplier_profile.partner)
        .prefetch_related('stockrecords', 'categories', 'attribute_values__attribute', 'images')
        .distinct()
    )


def _build_supplier_product_detail(product, supplier_profile):
    detail = _build_product_detail(product)
    detail['supplier'] = {
        'partner_id': supplier_profile.partner.id,
        'partner_name': supplier_profile.partner.name,
        'partner_code': supplier_profile.partner.code,
        'status': supplier_profile.status,
    }
    detail['offer'] = SupplierProductListSerializer.build_offer(product, supplier_profile)
    detail['shared_catalog'] = product.stockrecords.exclude(partner=supplier_profile.partner).exists()
    return detail


class SupplierProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        supplier_profile = getattr(request.user, 'supplier_profile', None)
        if supplier_profile is None:
            return Response({'supplier': None, 'can_apply': True})
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data, 'can_apply': False})

    def post(self, request):
        if hasattr(request.user, 'supplier_profile'):
            return Response(
                {
                    'error': {
                        'code': 'supplier_profile_exists',
                        'detail': 'This account already has a supplier profile.',
                        'status': 400,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SupplierProfileWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        supplier_profile = serializer.save()
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        supplier_profile = getattr(request.user, 'supplier_profile', None)
        if supplier_profile is None:
            return Response(
                {
                    'error': {
                        'code': 'supplier_profile_missing',
                        'detail': 'Create a supplier profile before updating it.',
                        'status': 404,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SupplierProfileWriteSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        supplier_profile = serializer.save()
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data})


class SupplierDashboardAPIView(APIView):
    permission_classes = [SupplierOnlyPermission]

    def get(self, request):
        return Response(SupplierDashboardSerializer(request.user.supplier_profile).data)


class SupplierProductCollectionAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def get(self, request):
        supplier_profile = request.user.supplier_profile
        queryset = _supplier_product_queryset(supplier_profile).order_by('-date_updated', 'title')
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 24) or 24), 1), 60)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': {
                        'code': 'invalid_pagination',
                        'detail': 'Page and page_size must be integers.',
                        'status': 400,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = SupplierProductListSerializer(page_obj.object_list, many=True, context={'supplier_profile': supplier_profile})
        return Response(
            {
                'results': serializer.data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )

    def post(self, request):
        supplier_profile = request.user.supplier_profile
        serializer = SupplierProductWriteSerializer(data=request.data, context={'request': request, 'supplier_profile': supplier_profile})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product.id)
        return Response({'product': _build_supplier_product_detail(product, supplier_profile)}, status=status.HTTP_201_CREATED)


class SupplierProductDetailAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def get(self, request, product_id: int):
        supplier_profile = request.user.supplier_profile
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        return Response({'product': _build_supplier_product_detail(product, supplier_profile)})

    def patch(self, request, product_id: int):
        supplier_profile = request.user.supplier_profile
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        serializer = SupplierProductWriteSerializer(
            instance=product,
            data=request.data,
            partial=True,
            context={'request': request, 'supplier_profile': supplier_profile},
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product.id)
        return Response({'product': _build_supplier_product_detail(product, supplier_profile)})

    @transaction.atomic
    def delete(self, request, product_id: int):
        supplier_profile = request.user.supplier_profile
        StockRecord = apps.get_model('partner', 'StockRecord')
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        stockrecords = product.stockrecords.filter(partner=supplier_profile.partner)
        deleted_offers = stockrecords.count()
        stockrecords.delete()

        if not StockRecord.objects.filter(product=product).exists():
            product.delete()
            product_deleted = True
        else:
            product_deleted = False

        return Response(
            {
                'detail': 'Supplier offer removed successfully.',
                'deleted_offers': deleted_offers,
                'product_deleted': product_deleted,
            }
        )


class SupplierAdminCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
        queryset = SupplierProfile.objects.select_related('user', 'partner').order_by('company_name', 'id')
        status_filter = (request.query_params.get('status') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response({'results': SupplierProfileSerializer(queryset, many=True).data})


class SupplierAdminDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, supplier_id: int):
        SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
        supplier_profile = get_object_or_404(SupplierProfile.objects.select_related('user', 'partner'), id=supplier_id)
        serializer = SupplierAdminStatusSerializer(instance=supplier_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier_profile = serializer.save()
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data})
