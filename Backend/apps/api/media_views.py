from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from rest_framework import permissions, serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event

from .serializers import ProductImageUploadSerializer
from .views import _product_queryset


def _serialize_media_image(image) -> dict:
    product = image.product
    original = getattr(image, 'original', None)
    filename = getattr(original, 'name', '') or ''
    return {
        'id': image.id,
        'name': filename.rsplit('/', 1)[-1] or f'image-{image.id}',
        'url': original.url if original else '',
        'alt': image.caption or product.title or '',
        'productId': product.id,
        'productTitle': product.title,
        'displayOrder': image.display_order,
        'createdAt': getattr(image, 'date_created', None),
    }


class AdminMediaUploadSerializer(ProductImageUploadSerializer):
    product_id = serializers.IntegerField(min_value=1)


class AdminMediaCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        queryset = ProductImage.objects.select_related('product').order_by('-id')

        query = (request.query_params.get('q') or '').strip()
        product_id = (request.query_params.get('product_id') or '').strip()
        if query:
            queryset = queryset.filter(
                Q(caption__icontains=query)
                | Q(original__icontains=query)
                | Q(product__title__icontains=query)
                | Q(product__upc__icontains=query)
            )
        if product_id:
            queryset = queryset.filter(product_id=product_id)

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
                'results': [_serialize_media_image(image) for image in page_obj.object_list],
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': ProductImage.objects.count(),
                    'matching': paginator.count,
                },
            }
        )

    def post(self, request):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        serializer = AdminMediaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(_product_queryset(include_hidden=True), id=serializer.validated_data['product_id'])
        uploaded_file = serializer.validated_data['image']
        alt = (serializer.validated_data.get('alt') or product.title or '').strip()
        filename_root = slugify(product.title or product.upc or f'product-{product.id}') or f'product-{product.id}'
        upload_name = getattr(uploaded_file, 'name', '') or f'{filename_root}.webp'
        final_name = upload_name if '.' in upload_name else f'{filename_root}.webp'

        product_image = ProductImage(product=product, caption=alt, display_order=product.images.count())
        product_image.original.save(final_name, ContentFile(uploaded_file.read()), save=False)
        product_image.save()

        record_audit_event(
            event_type='catalog.media_uploaded',
            request=request,
            actor=request.user,
            target=product,
            message='Admin uploaded media asset.',
            metadata={'image_id': product_image.id, 'product_id': product.id, 'filename': final_name},
        )
        return Response({'media': _serialize_media_image(product_image)}, status=status.HTTP_201_CREATED)


class AdminMediaDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, image_id: int):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        image = get_object_or_404(ProductImage.objects.select_related('product'), id=image_id)
        product = image.product
        metadata = {
            'image_id': image.id,
            'product_id': product.id,
            'filename': getattr(getattr(image, 'original', None), 'name', ''),
        }
        image.delete()
        record_audit_event(
            event_type='catalog.media_deleted',
            request=request,
            actor=request.user,
            target=product,
            message='Admin deleted media asset.',
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
