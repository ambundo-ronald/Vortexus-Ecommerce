from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.notifications.services import (
    create_admin_notification,
    queue_shipping_update_email,
    queue_supplier_application_submitted_email,
    queue_supplier_status_changed_email,
)

from .account_manager_scope import assigned_supplier_queryset, can_access_all_admin_data, is_account_manager
from .supplier_order_serializers import (
    SupplierOrderDetailSerializer,
    SupplierOrderLineStatusSerializer,
    SupplierOrderListSerializer,
)
from .supplier_serializers import (
    SupplierAdminCreateSerializer,
    SupplierAdminStatusSerializer,
    SupplierDashboardSerializer,
    SupplierProductOfferListSerializer,
    SupplierProductOfferModerationSerializer,
    SupplierProductOfferWriteSerializer,
    SupplierProductModerationListSerializer,
    SupplierProductModerationSerializer,
    SupplierProductListSerializer,
    SupplierProductRequestListSerializer,
    SupplierProductRequestModerationSerializer,
    SupplierProductRequestWriteSerializer,
    SupplierProductWriteSerializer,
    SupplierProfileSerializer,
    SupplierProfileWriteSerializer,
)
from .serializers import ProductImageUploadSerializer
from .media_utils import delete_product_image_with_file
from .views import _build_product_detail, _serialize_product_image


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
        .select_related('supplier_submission__reviewed_by')
        .prefetch_related('stockrecords', 'categories', 'attribute_values__attribute', 'images')
        .distinct()
    )


def _supplier_offer_queryset(supplier_profile):
    SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
    return (
        SupplierProductOffer.objects.filter(supplier=supplier_profile)
        .select_related('supplier', 'supplier__user', 'supplier__partner', 'product', 'stockrecord', 'reviewed_by')
        .prefetch_related('product__stockrecords', 'product__categories', 'product__images')
        .order_by('-updated_at', '-id')
    )


def _supplier_product_request_queryset(supplier_profile):
    SupplierProductRequest = apps.get_model('marketplace', 'SupplierProductRequest')
    return (
        SupplierProductRequest.objects.filter(supplier=supplier_profile)
        .select_related('supplier', 'supplier__user', 'supplier__partner', 'linked_product', 'reviewed_by')
        .prefetch_related('linked_product__stockrecords', 'linked_product__categories', 'linked_product__images')
        .order_by('-updated_at', '-id')
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


def _supplier_order_queryset(supplier_profile):
    SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')
    return (
        SupplierOrderGroup.objects.filter(partner=supplier_profile.partner)
        .select_related('partner', 'order__user', 'order__shipping_address')
        .prefetch_related('order__lines__partner', 'order__lines__product', 'order__status_changes')
        .order_by('-order__date_placed', '-id')
    )


def _recompute_order_status(order):
    Line = apps.get_model('order', 'Line')
    statuses = {
        ((status or '').strip().lower() or 'pending')
        for status in Line.objects.filter(order=order).values_list('status', flat=True)
    }

    if statuses == {'delivered'}:
        return 'Delivered'
    if statuses == {'cancelled'}:
        return 'Cancelled'
    if statuses.issubset({'shipped', 'delivered'}):
        return 'Shipped'
    if 'shipped' in statuses or 'delivered' in statuses:
        return 'Partially Shipped'
    if statuses == {'packed'}:
        return 'Packed'
    if 'packed' in statuses:
        return 'Processing'
    if statuses == {'processing'}:
        return 'Processing'
    return 'Pending'


def _recompute_supplier_group_status(order, partner_id: int):
    Line = apps.get_model('order', 'Line')
    statuses = {
        ((status or '').strip().lower() or 'pending')
        for status in Line.objects.filter(order=order, partner_id=partner_id).values_list('status', flat=True)
    }
    if statuses == {'delivered'}:
        return 'delivered'
    if statuses == {'cancelled'}:
        return 'cancelled'
    if statuses.issubset({'shipped', 'delivered'}):
        return 'shipped'
    if 'shipped' in statuses or 'delivered' in statuses:
        return 'partially_shipped'
    if statuses == {'packed'}:
        return 'packed'
    if 'packed' in statuses:
        return 'processing'
    if statuses == {'processing'}:
        return 'processing'
    return 'pending'


class SupplierProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_throttles(self):
        if self.request.method == 'POST':
            self.throttle_scope = 'supplier_apply'
            return [ScopedRateThrottle()]
        return super().get_throttles()

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
        record_audit_event(
            event_type='supplier.profile_created',
            request=request,
            actor=request.user,
            target=supplier_profile,
            message='Supplier profile application created.',
            metadata={'company_name': supplier_profile.company_name, 'status': supplier_profile.status},
        )
        create_admin_notification(
            event_type='supplier_application_submitted',
            event_key=f'supplier-application:{supplier_profile.id}',
            title='Supplier application submitted',
            message=f'{supplier_profile.company_name} applied to sell on the marketplace.',
            severity='warning',
            action_url=f'/suppliers?supplier={supplier_profile.id}',
            related_object_type='supplier_profile',
            related_object_id=str(supplier_profile.id),
            metadata={'supplier_id': supplier_profile.id, 'company_name': supplier_profile.company_name, 'user_id': request.user.id},
        )
        queue_supplier_application_submitted_email(supplier_profile)
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
        previous_status = supplier_profile.status
        supplier_profile = serializer.save()
        if supplier_profile.status != previous_status:
            queue_supplier_status_changed_email(supplier_profile)
        record_audit_event(
            event_type='supplier.profile_updated',
            request=request,
            actor=request.user,
            target=supplier_profile,
            message='Supplier profile updated.',
            metadata={'previous_status': previous_status, 'current_status': supplier_profile.status},
        )
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data})


class SupplierDashboardAPIView(APIView):
    permission_classes = [SupplierOnlyPermission]

    def get(self, request):
        supplier_profile = request.user.supplier_profile
        data = SupplierDashboardSerializer(supplier_profile).data
        supplier_orders = _supplier_order_queryset(supplier_profile)
        data['orders'] = {
            'count': supplier_orders.count(),
            'open_count': supplier_orders.exclude(status__in=['delivered', 'cancelled']).count(),
        }
        return Response(data)


class SupplierProductOfferCollectionAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def get(self, request):
        supplier_profile = request.user.supplier_profile
        queryset = _supplier_offer_queryset(supplier_profile)
        status_filter = (request.query_params.get('status') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
        except (TypeError, ValueError):
            return Response({'detail': 'Page and page_size must be integers.'}, status=status.HTTP_400_BAD_REQUEST)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': SupplierProductOfferListSerializer(page_obj.object_list, many=True).data,
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
        serializer = SupplierProductOfferWriteSerializer(
            data=request.data,
            context={'request': request, 'supplier_profile': supplier_profile},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        record_audit_event(
            event_type='supplier.offer_submitted',
            request=request,
            actor=request.user,
            target=offer.product,
            message='Supplier submitted a product offer.',
            metadata={'offer_id': offer.id, 'supplier_id': supplier_profile.id, 'product_id': offer.product_id},
        )
        return Response({'offer': SupplierProductOfferListSerializer(offer).data}, status=status.HTTP_201_CREATED)


class SupplierProductOfferDetailAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def patch(self, request, offer_id: int):
        supplier_profile = request.user.supplier_profile
        offer = get_object_or_404(_supplier_offer_queryset(supplier_profile), id=offer_id)
        data = request.data.copy()
        data['product_id'] = offer.product_id
        serializer = SupplierProductOfferWriteSerializer(
            instance=offer,
            data=data,
            partial=True,
            context={'request': request, 'supplier_profile': supplier_profile},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        record_audit_event(
            event_type='supplier.offer_updated',
            request=request,
            actor=request.user,
            target=offer.product,
            message='Supplier updated a product offer.',
            metadata={'offer_id': offer.id, 'supplier_id': supplier_profile.id, 'product_id': offer.product_id},
        )
        return Response({'offer': SupplierProductOfferListSerializer(offer).data})

    def delete(self, request, offer_id: int):
        supplier_profile = request.user.supplier_profile
        offer = get_object_or_404(_supplier_offer_queryset(supplier_profile), id=offer_id)
        if offer.stockrecord_id:
            offer.stockrecord.num_in_stock = 0
            offer.stockrecord.save(update_fields=['num_in_stock'])
        offer.status = offer.STATUS_SUSPENDED
        offer.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Supplier offer suspended.'})


class SupplierProductRequestCollectionAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def get(self, request):
        supplier_profile = request.user.supplier_profile
        queryset = _supplier_product_request_queryset(supplier_profile)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
        except (TypeError, ValueError):
            return Response({'detail': 'Page and page_size must be integers.'}, status=status.HTTP_400_BAD_REQUEST)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': SupplierProductRequestListSerializer(page_obj.object_list, many=True).data,
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
        serializer = SupplierProductRequestWriteSerializer(
            data=request.data,
            context={'request': request, 'supplier_profile': supplier_profile},
        )
        serializer.is_valid(raise_exception=True)
        product_request = serializer.save()
        record_audit_event(
            event_type='supplier.product_request_submitted',
            request=request,
            actor=request.user,
            target=product_request,
            message='Supplier requested a new catalogue product.',
            metadata={'request_id': product_request.id, 'supplier_id': supplier_profile.id},
        )
        return Response({'request': SupplierProductRequestListSerializer(product_request).data}, status=status.HTTP_201_CREATED)


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
        record_audit_event(
            event_type='supplier.product_created',
            request=request,
            actor=request.user,
            target=product,
            message='Supplier created a product offer.',
            metadata={'partner_id': supplier_profile.partner_id, 'partner_name': supplier_profile.partner.name},
        )
        create_admin_notification(
            event_type='supplier_product_submitted',
            event_key=f'supplier-product:{product.id}',
            title='Supplier product pending review',
            message=f'{supplier_profile.company_name} submitted {product.title} for approval.',
            severity='warning',
            action_url=f'/supplier-product-reviews?product={product.id}',
            related_object_type='product',
            related_object_id=str(product.id),
            metadata={'supplier_id': supplier_profile.id, 'product_id': product.id, 'company_name': supplier_profile.company_name},
        )
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
        previous_title = product.title
        serializer = SupplierProductWriteSerializer(
            instance=product,
            data=request.data,
            partial=True,
            context={'request': request, 'supplier_profile': supplier_profile},
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product.id)
        record_audit_event(
            event_type='supplier.product_updated',
            request=request,
            actor=request.user,
            target=product,
            message='Supplier updated a product offer.',
            metadata={
                'partner_id': supplier_profile.partner_id,
                'previous_title': previous_title,
                'current_title': product.title,
            },
        )
        return Response({'product': _build_supplier_product_detail(product, supplier_profile)})

    @transaction.atomic
    def delete(self, request, product_id: int):
        supplier_profile = request.user.supplier_profile
        StockRecord = apps.get_model('partner', 'StockRecord')
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        metadata = {
            'partner_id': supplier_profile.partner_id,
            'partner_name': supplier_profile.partner.name,
            'product_id': product.id,
            'title': product.title,
            'upc': product.upc,
        }
        stockrecords = product.stockrecords.filter(partner=supplier_profile.partner)
        deleted_offers = stockrecords.count()
        stockrecords.delete()

        if not StockRecord.objects.filter(product=product).exists():
            product.delete()
            product_deleted = True
        else:
            product_deleted = False
        metadata.update({'deleted_offers': deleted_offers, 'product_deleted': product_deleted})
        record_audit_event(
            event_type='supplier.product_deleted',
            request=request,
            actor=request.user,
            message='Supplier removed a product offer.',
            metadata=metadata,
        )

        return Response(
            {
                'detail': 'Supplier offer removed successfully.',
                'deleted_offers': deleted_offers,
                'product_deleted': product_deleted,
            }
        )


class SupplierProductImageCollectionAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, product_id: int):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        supplier_profile = request.user.supplier_profile
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        serializer = ProductImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['image']
        alt = (serializer.validated_data.get('alt') or product.title or '').strip()
        filename_root = slugify(product.title or product.upc or f'product-{product.id}') or f'product-{product.id}'
        upload_name = getattr(uploaded_file, 'name', '') or f'{filename_root}.webp'
        final_name = upload_name if '.' in upload_name else f'{filename_root}.webp'

        product_image = ProductImage(product=product, caption=alt, display_order=product.images.count())
        product_image.original.save(final_name, ContentFile(uploaded_file.read()), save=False)
        product_image.save()

        record_audit_event(
            event_type='supplier.product_image_uploaded',
            request=request,
            actor=request.user,
            target=product,
            message='Supplier uploaded product image.',
            metadata={
                'partner_id': supplier_profile.partner_id,
                'image_id': product_image.id,
                'product_id': product.id,
                'filename': final_name,
            },
        )
        return Response({'image': _serialize_product_image(product_image, fallback_alt=product.title)}, status=status.HTTP_201_CREATED)


class SupplierProductImageDetailAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    def delete(self, request, product_id: int, image_id: int):
        supplier_profile = request.user.supplier_profile
        product = get_object_or_404(_supplier_product_queryset(supplier_profile), id=product_id)
        image = get_object_or_404(product.images.all(), id=image_id)
        filename = delete_product_image_with_file(image)

        record_audit_event(
            event_type='supplier.product_image_deleted',
            request=request,
            actor=request.user,
            target=product,
            message='Supplier deleted product image.',
            metadata={
                'partner_id': supplier_profile.partner_id,
                'image_id': image_id,
                'product_id': product.id,
                'filename': filename,
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def _supplier_product_submission_queryset():
    SupplierProductSubmission = apps.get_model('marketplace', 'SupplierProductSubmission')
    return (
        SupplierProductSubmission.objects.select_related(
            'supplier',
            'supplier__user',
            'supplier__partner',
            'product',
            'reviewed_by',
        )
        .prefetch_related('product__stockrecords', 'product__categories', 'product__images', 'product__attribute_values__attribute')
        .order_by('-updated_at', '-id')
    )


def _admin_supplier_offer_queryset(user):
    SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
    queryset = (
        SupplierProductOffer.objects.select_related(
            'supplier',
            'supplier__user',
            'supplier__partner',
            'product',
            'stockrecord',
            'reviewed_by',
        )
        .prefetch_related('product__stockrecords', 'product__categories', 'product__images')
        .order_by('-updated_at', '-id')
    )
    if is_account_manager(user):
        queryset = queryset.filter(supplier__account_manager=user)
    return queryset


def _admin_supplier_product_request_queryset(user):
    SupplierProductRequest = apps.get_model('marketplace', 'SupplierProductRequest')
    queryset = (
        SupplierProductRequest.objects.select_related(
            'supplier',
            'supplier__user',
            'supplier__partner',
            'linked_product',
            'reviewed_by',
        )
        .prefetch_related('linked_product__stockrecords', 'linked_product__categories', 'linked_product__images')
        .order_by('-updated_at', '-id')
    )
    if is_account_manager(user):
        queryset = queryset.filter(supplier__account_manager=user)
    return queryset


class SupplierOfferModerationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _admin_supplier_offer_queryset(request.user)
        status_filter = (request.query_params.get('status') or '').strip()
        supplier_id = (request.query_params.get('supplier_id') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 24) or 24), 1), 100)
        except (TypeError, ValueError):
            return Response({'detail': 'Page and page_size must be integers.'}, status=status.HTTP_400_BAD_REQUEST)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': SupplierProductOfferListSerializer(page_obj.object_list, many=True).data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class SupplierOfferModerationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, offer_id: int):
        offer = get_object_or_404(_admin_supplier_offer_queryset(request.user), id=offer_id)
        previous_status = offer.status
        serializer = SupplierProductOfferModerationSerializer(instance=offer, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        record_audit_event(
            event_type='supplier.offer_moderation_changed',
            request=request,
            actor=request.user,
            target=offer.product,
            message='Supplier product offer moderation status updated.',
            metadata={
                'offer_id': offer.id,
                'supplier_id': offer.supplier_id,
                'product_id': offer.product_id,
                'previous_status': previous_status,
                'current_status': offer.status,
                'stockrecord_id': offer.stockrecord_id,
            },
        )
        return Response({'offer': SupplierProductOfferListSerializer(offer).data})


class SupplierProductRequestModerationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _admin_supplier_product_request_queryset(request.user)
        status_filter = (request.query_params.get('status') or '').strip()
        supplier_id = (request.query_params.get('supplier_id') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 24) or 24), 1), 100)
        except (TypeError, ValueError):
            return Response({'detail': 'Page and page_size must be integers.'}, status=status.HTTP_400_BAD_REQUEST)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': SupplierProductRequestListSerializer(page_obj.object_list, many=True).data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class SupplierProductRequestModerationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, request_id: int):
        product_request = get_object_or_404(_admin_supplier_product_request_queryset(request.user), id=request_id)
        previous_status = product_request.status
        serializer = SupplierProductRequestModerationSerializer(instance=product_request, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product_request = serializer.save()
        record_audit_event(
            event_type='supplier.product_request_moderation_changed',
            request=request,
            actor=request.user,
            target=product_request,
            message='Supplier product request moderation status updated.',
            metadata={
                'request_id': product_request.id,
                'supplier_id': product_request.supplier_id,
                'linked_product_id': product_request.linked_product_id,
                'previous_status': previous_status,
                'current_status': product_request.status,
            },
        )
        return Response({'request': SupplierProductRequestListSerializer(product_request).data})


class SupplierProductModerationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _supplier_product_submission_queryset()
        if is_account_manager(request.user):
            queryset = queryset.filter(supplier__account_manager=request.user)
        status_filter = (request.query_params.get('status') or '').strip()
        supplier_id = (request.query_params.get('supplier_id') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 24) or 24), 1), 100)
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
        return Response(
            {
                'results': SupplierProductModerationListSerializer(page_obj.object_list, many=True).data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
            }
        )


class SupplierProductModerationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, submission_id: int):
        queryset = _supplier_product_submission_queryset()
        if is_account_manager(request.user):
            queryset = queryset.filter(supplier__account_manager=request.user)
        submission = get_object_or_404(queryset, id=submission_id)
        return Response({'submission': SupplierProductModerationListSerializer(submission).data})

    def patch(self, request, submission_id: int):
        queryset = _supplier_product_submission_queryset()
        if is_account_manager(request.user):
            queryset = queryset.filter(supplier__account_manager=request.user)
        submission = get_object_or_404(queryset, id=submission_id)
        previous_status = submission.status
        serializer = SupplierProductModerationSerializer(instance=submission, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        record_audit_event(
            event_type='supplier.product_moderation_changed',
            request=request,
            actor=request.user,
            target=submission.product,
            message='Supplier product moderation status updated.',
            metadata={
                'submission_id': submission.id,
                'supplier_id': submission.supplier_id,
                'supplier_name': submission.supplier.company_name,
                'product_id': submission.product_id,
                'previous_status': previous_status,
                'current_status': submission.status,
            },
        )
        return Response({'submission': SupplierProductModerationListSerializer(submission).data})


class SupplierAdminCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = assigned_supplier_queryset(request.user).order_by('company_name', 'id')
        status_filter = (request.query_params.get('status') or '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response({'results': SupplierProfileSerializer(queryset, many=True).data})

    def post(self, request):
        if not can_access_all_admin_data(request.user):
            return Response(
                {
                    'error': {
                        'code': 'platform_admin_required',
                        'detail': 'Only a platform admin can create supplier accounts.',
                        'status': 403,
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SupplierAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier_profile = serializer.save()
        record_audit_event(
            event_type='supplier.admin_created',
            request=request,
            actor=request.user,
            target=supplier_profile,
            message='Admin created a supplier profile.',
            metadata={
                'supplier_id': supplier_profile.id,
                'company_name': supplier_profile.company_name,
                'email': supplier_profile.user.email,
                'status': supplier_profile.status,
            },
        )
        queue_supplier_status_changed_email(supplier_profile)
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data}, status=status.HTTP_201_CREATED)


class SupplierAdminDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, supplier_id: int):
        supplier_profile = get_object_or_404(assigned_supplier_queryset(request.user), id=supplier_id)
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data})

    def patch(self, request, supplier_id: int):
        supplier_profile = get_object_or_404(assigned_supplier_queryset(request.user), id=supplier_id)
        previous_status = supplier_profile.status
        data = request.data.copy()
        if not can_access_all_admin_data(request.user):
            data.pop('account_manager_id', None)
        serializer = SupplierAdminStatusSerializer(instance=supplier_profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier_profile = serializer.save()
        if supplier_profile.status != previous_status:
            queue_supplier_status_changed_email(supplier_profile)
        record_audit_event(
            event_type='supplier.status_changed',
            request=request,
            actor=request.user,
            target=supplier_profile,
            message='Supplier status updated by staff.',
            metadata={'previous_status': previous_status, 'current_status': supplier_profile.status},
        )
        return Response({'supplier': SupplierProfileSerializer(supplier_profile).data})


class SupplierOrderCollectionAPIView(APIView):
    permission_classes = [SupplierOnlyPermission]

    def get(self, request):
        supplier_profile = request.user.supplier_profile
        queryset = _supplier_order_queryset(supplier_profile)
        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
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
        serializer = SupplierOrderListSerializer(page_obj.object_list, many=True, context={'supplier_profile': supplier_profile})
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


class SupplierOrderDetailAPIView(APIView):
    permission_classes = [SupplierOnlyPermission]

    def get(self, request, order_number: str):
        supplier_profile = request.user.supplier_profile
        group = get_object_or_404(_supplier_order_queryset(supplier_profile), order__number=order_number)
        return Response({'order': SupplierOrderDetailSerializer(group, context={'supplier_profile': supplier_profile}).data})


class SupplierOrderLineStatusAPIView(APIView):
    permission_classes = [ApprovedSupplierWritePermission]

    @transaction.atomic
    def post(self, request, order_number: str, line_id: int):
        supplier_profile = request.user.supplier_profile
        Order = apps.get_model('order', 'Order')
        Line = apps.get_model('order', 'Line')
        OrderStatusChange = apps.get_model('order', 'OrderStatusChange')
        ShippingEventType = apps.get_model('order', 'ShippingEventType')
        ShippingEvent = apps.get_model('order', 'ShippingEvent')
        ShippingEventQuantity = apps.get_model('order', 'ShippingEventQuantity')
        SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')

        order = get_object_or_404(Order.objects.prefetch_related('lines').select_related('user'), number=order_number, lines__partner=supplier_profile.partner)
        line = get_object_or_404(Line.objects.select_related('order', 'partner'), id=line_id, order=order, partner=supplier_profile.partner)
        group = get_object_or_404(SupplierOrderGroup, order=order, partner=supplier_profile.partner)
        serializer = SupplierOrderLineStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_line_status = line.status or ''
        new_line_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')
        tracking_reference = serializer.validated_data.get('tracking_reference', '')

        line.status = new_line_status
        line.save(update_fields=['status'])

        if old_line_status not in {'shipped', 'delivered'} and new_line_status in {'shipped', 'delivered'}:
            if getattr(line, 'num_allocated', 0):
                line.consume_allocation(line.num_allocated)
        elif old_line_status not in {'cancelled', 'shipped', 'delivered'} and new_line_status == 'cancelled':
            if getattr(line, 'num_allocated', 0):
                line.cancel_allocation(line.num_allocated)

        event_type, _ = ShippingEventType.objects.get_or_create(
            code=new_line_status,
            defaults={'name': new_line_status.replace('_', ' ').title()},
        )
        notes = f'Supplier {supplier_profile.company_name} updated line {line.id} to {new_line_status}.'
        if tracking_reference:
            notes += f' Tracking: {tracking_reference}.'
        if note:
            notes += f' Note: {note}'
        event = ShippingEvent.objects.create(order=order, event_type=event_type, notes=notes)
        ShippingEventQuantity.objects.create(event=event, line=line, quantity=line.quantity)

        group.status = _recompute_supplier_group_status(order, supplier_profile.partner_id)
        if tracking_reference:
            group.tracking_reference = tracking_reference
        if note:
            group.notes = note
        group.save(update_fields=['status', 'tracking_reference', 'notes', 'updated_at'])

        new_order_status = _recompute_order_status(order)
        if (order.status or '') != new_order_status:
            OrderStatusChange.objects.create(order=order, old_status=order.status or '', new_status=new_order_status)
            previous_order_status = order.status or ''
            order.status = new_order_status
            order.save(update_fields=['status'])
            record_audit_event(
                event_type='orders.status_changed',
                request=request,
                actor=request.user,
                target=order,
                message='Order status updated after supplier fulfillment change.',
                metadata={'order_number': order.number, 'previous_status': previous_order_status, 'current_status': new_order_status},
            )

        if new_line_status in {'shipped', 'delivered'}:
            queue_shipping_update_email(
                order,
                status_label=new_line_status.replace('_', ' ').title(),
                tracking_reference=tracking_reference,
                note=note or f'Updated by supplier {supplier_profile.company_name}.',
            )
        record_audit_event(
            event_type='orders.line_status_changed',
            request=request,
            actor=request.user,
            target=line,
            message='Supplier updated an order line status.',
            metadata={
                'order_number': order.number,
                'line_id': line.id,
                'supplier_group_id': group.id,
                'previous_status': old_line_status,
                'current_status': new_line_status,
                'tracking_reference': tracking_reference,
            },
        )

        return Response(
            {
                'detail': 'Supplier line status updated successfully.',
                'order_number': order.number,
                'line': {
                    'id': line.id,
                    'old_status': old_line_status,
                    'new_status': new_line_status,
                },
                'supplier_group': {
                    'id': group.id,
                    'status': group.status,
                    'tracking_reference': group.tracking_reference,
                },
                'order_status': order.status,
            }
        )
