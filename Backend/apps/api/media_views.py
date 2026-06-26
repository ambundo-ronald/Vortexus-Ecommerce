from django.apps import apps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
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
from .media_utils import delete_product_image_with_file
from .views import _product_queryset


def _serialize_media_image(image) -> dict:
    product = image.product
    original = getattr(image, 'original', None)
    filename = getattr(original, 'name', '') or ''
    return {
        'id': f'product-{image.id}',
        'numericId': image.id,
        'mediaType': 'product',
        'category': 'product',
        'name': filename.rsplit('/', 1)[-1] or f'image-{image.id}',
        'url': original.url if original else '',
        'alt': image.caption or product.title or '',
        'productId': product.id,
        'productTitle': product.title,
        'displayOrder': image.display_order,
        'createdAt': getattr(image, 'date_created', None),
    }


def _serialize_marketing_asset(asset) -> dict:
    filename = getattr(asset.image, 'name', '') or ''
    return {
        'id': f'marketing_block-{asset.id}',
        'numericId': asset.id,
        'mediaType': 'marketing_block',
        'category': asset.category,
        'name': filename.rsplit('/', 1)[-1] or f'marketing-{asset.id}',
        'url': asset.image.url if asset.image else '',
        'alt': asset.alt_text or asset.title or '',
        'productId': None,
        'productTitle': 'Marketing block',
        'displayOrder': 0,
        'createdAt': asset.created_at,
    }


class AdminMediaUploadSerializer(ProductImageUploadSerializer):
    product_id = serializers.IntegerField(min_value=1, required=False)
    media_type = serializers.ChoiceField(choices=['product', 'marketing_block'], required=False, default='product')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('media_type', 'product') == 'product' and not attrs.get('product_id'):
            raise serializers.ValidationError({'product_id': 'Product ID is required for product media.'})
        return attrs


class AdminMediaCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        MarketingMediaAsset = apps.get_model('content', 'MarketingMediaAsset')

        query = (request.query_params.get('q') or '').strip()
        product_id = (request.query_params.get('product_id') or '').strip()
        media_type = (request.query_params.get('media_type') or '').strip()

        product_queryset = ProductImage.objects.select_related('product').order_by('-id')
        marketing_queryset = MarketingMediaAsset.objects.order_by('-created_at', '-id')
        if query:
            product_queryset = product_queryset.filter(
                Q(caption__icontains=query)
                | Q(original__icontains=query)
                | Q(product__title__icontains=query)
                | Q(product__upc__icontains=query)
            )
            marketing_queryset = marketing_queryset.filter(
                Q(title__icontains=query)
                | Q(alt_text__icontains=query)
                | Q(image__icontains=query)
                | Q(category__icontains=query)
            )
        if product_id:
            product_queryset = product_queryset.filter(product_id=product_id)
            marketing_queryset = marketing_queryset.none()
        if media_type == 'product':
            marketing_queryset = marketing_queryset.none()
        elif media_type == 'marketing_block':
            product_queryset = product_queryset.none()

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

        items = [_serialize_media_image(image) for image in product_queryset[:500]]
        items.extend(_serialize_marketing_asset(asset) for asset in marketing_queryset[:500])
        items.sort(key=lambda item: str(item.get('createdAt') or ''), reverse=True)

        paginator = Paginator(items, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': list(page_obj.object_list),
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': ProductImage.objects.count() + MarketingMediaAsset.objects.count(),
                    'matching': paginator.count,
                },
            }
        )

    def post(self, request):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        MarketingMediaAsset = apps.get_model('content', 'MarketingMediaAsset')
        serializer = AdminMediaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data['image']
        media_type = serializer.validated_data.get('media_type', 'product')

        if media_type == 'marketing_block':
            alt = (serializer.validated_data.get('alt') or '').strip()
            title = alt or getattr(uploaded_file, 'name', '') or 'Marketing block image'
            asset = MarketingMediaAsset.objects.create(
                category=MarketingMediaAsset.CATEGORY_MARKETING_BLOCK,
                title=title[:160],
                alt_text=alt[:160],
                uploaded_by=request.user,
            )
            filename_root = slugify(title) or f'marketing-block-{asset.id}'
            upload_name = getattr(uploaded_file, 'name', '') or f'{filename_root}.webp'
            final_name = upload_name if '.' in upload_name else f'{filename_root}.webp'
            asset.image.save(final_name, ContentFile(uploaded_file.read()), save=True)
            record_audit_event(
                event_type='content.marketing_media_uploaded',
                request=request,
                actor=request.user,
                target=asset,
                message='Admin uploaded marketing media asset.',
                metadata={'asset_id': asset.id, 'filename': final_name},
            )
            return Response({'media': _serialize_marketing_asset(asset)}, status=status.HTTP_201_CREATED)

        product = get_object_or_404(_product_queryset(include_hidden=True), id=serializer.validated_data['product_id'])
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

    def delete(self, request, image_id: str):
        ProductImage = apps.get_model('catalogue', 'ProductImage')
        MarketingMediaAsset = apps.get_model('content', 'MarketingMediaAsset')
        raw_id = str(image_id)
        if raw_id.startswith('marketing_block-'):
            asset_id = raw_id.removeprefix('marketing_block-')
            asset = get_object_or_404(MarketingMediaAsset, id=asset_id)
            filename = getattr(asset.image, 'name', '') or ''
            if filename and default_storage.exists(filename):
                default_storage.delete(filename)
            asset.delete()
            record_audit_event(
                event_type='content.marketing_media_deleted',
                request=request,
                actor=request.user,
                message='Admin deleted marketing media asset.',
                metadata={'asset_id': asset_id, 'filename': filename},
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        product_image_id = raw_id.removeprefix('product-')
        image = get_object_or_404(ProductImage.objects.select_related('product'), id=product_image_id)
        product = image.product
        image_id = image.id
        filename = delete_product_image_with_file(image)
        metadata = {
            'image_id': image_id,
            'product_id': product.id,
            'filename': filename,
        }
        record_audit_event(
            event_type='catalog.media_deleted',
            request=request,
            actor=request.user,
            target=product,
            message='Admin deleted media asset.',
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
