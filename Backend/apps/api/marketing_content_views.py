from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event
from apps.content.models import MarketingBlock

from .marketing_content_serializers import (
    IMAGE_PLACEMENTS,
    MarketingBlockSerializer,
    PublicMarketingBlockSerializer,
)


def _parse_pagination(request, *, default_page_size=24, max_page_size=100):
    try:
        page = max(int(request.query_params.get('page', 1) or 1), 1)
        page_size = min(max(int(request.query_params.get('page_size', default_page_size) or default_page_size), 1), max_page_size)
    except (TypeError, ValueError):
        return None, Response(
            {
                'error': {
                    'code': 'invalid_pagination',
                    'detail': 'Page and page_size must be integers.',
                    'status': 400,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return (page, page_size), None


class AdminMarketingBlockCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = MarketingBlock.objects.order_by('placement', 'sort_order', 'id')
        query = (request.query_params.get('q') or '').strip()
        placement = (request.query_params.get('placement') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(slug__icontains=query)
                | Q(headline__icontains=query)
                | Q(body__icontains=query)
                | Q(placement__icontains=query)
            )
        if placement:
            queryset = queryset.filter(placement=placement)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        pagination, error_response = _parse_pagination(request)
        if error_response:
            return error_response
        page, page_size = pagination

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return Response(
            {
                'results': MarketingBlockSerializer(page_obj.object_list, many=True).data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': MarketingBlock.objects.count(),
                    'active': MarketingBlock.objects.filter(is_active=True).count(),
                    'matching': paginator.count,
                },
                'placements': [{'value': value, 'label': label} for value, label in MarketingBlock.PLACEMENT_CHOICES],
            }
        )

    def post(self, request):
        serializer = MarketingBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        block = serializer.save()
        record_audit_event(
            event_type='content.marketing_block_created',
            request=request,
            actor=request.user,
            target=block,
            message='Admin created storefront marketing block.',
            metadata={'placement': block.placement, 'slug': block.slug},
        )
        return Response({'block': MarketingBlockSerializer(block).data}, status=status.HTTP_201_CREATED)


class AdminMarketingBlockDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, block_id: int):
        block = get_object_or_404(MarketingBlock, id=block_id)
        return Response({'block': MarketingBlockSerializer(block).data})

    def patch(self, request, block_id: int):
        block = get_object_or_404(MarketingBlock, id=block_id)
        serializer = MarketingBlockSerializer(block, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        block = serializer.save()
        record_audit_event(
            event_type='content.marketing_block_updated',
            request=request,
            actor=request.user,
            target=block,
            message='Admin updated storefront marketing block.',
            metadata={'placement': block.placement, 'slug': block.slug},
        )
        return Response({'block': MarketingBlockSerializer(block).data})

    def delete(self, request, block_id: int):
        block = get_object_or_404(MarketingBlock, id=block_id)
        metadata = {'placement': block.placement, 'slug': block.slug, 'title': block.title}
        block.delete()
        record_audit_event(
            event_type='content.marketing_block_deleted',
            request=request,
            actor=request.user,
            message='Admin deleted storefront marketing block.',
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicMarketingBlockCollectionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        queryset = MarketingBlock.objects.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gt=now),
        ).order_by('placement', 'sort_order', 'id')

        placement = (request.query_params.get('placement') or '').strip()
        if placement:
            queryset = queryset.filter(placement=placement)

        renderable_blocks = []
        for block in queryset.iterator():
            if block.placement in IMAGE_PLACEMENTS and not (block.image_url or '').strip():
                continue
            if block.placement == MarketingBlock.PLACEMENT_TOP_CATEGORY and not (block.cta_url or '').strip():
                continue
            renderable_blocks.append(block)
            if len(renderable_blocks) >= 300:
                break

        results = PublicMarketingBlockSerializer(renderable_blocks, many=True).data
        grouped = {
            value: [block for block in results if block['placement'] == value]
            for value, _label in MarketingBlock.PLACEMENT_CHOICES
        }

        return Response(
            {
                'results': results,
                'by_placement': grouped,
                'placements': [{'value': value, 'label': label} for value, label in MarketingBlock.PLACEMENT_CHOICES],
                'generated_at': now,
            }
        )
