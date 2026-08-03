from django.apps import apps
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.personal_shopper.models import ShopperList
from apps.recommendations.services import RecommendationService

from apps.common.currency import resolve_display_currency
from apps.common.taxes import resolve_tax_country
from .personal_shopper_serializers import (
    ShopperListWriteSerializer,
    replace_shopper_list_items,
    shopper_list_payload,
)


def _shopper_queryset():
    return (
        ShopperList.objects
        .select_related('customer', 'created_by')
        .prefetch_related('items__product__images', 'items__product__stockrecords', 'items__product__categories')
    )


def _recommendations(shopper_list, display_currency, tax_country_code):
    excluded = set(shopper_list.items.values_list('product_id', flat=True))
    results = []
    seen = set(excluded)
    service = RecommendationService()
    for product_id in excluded:
        for item in service.recommend_for_product(
            product_id,
            limit=6,
            display_currency=display_currency,
            tax_country_code=tax_country_code,
        ):
            if item['id'] in seen:
                continue
            seen.add(item['id'])
            results.append(item)
            if len(results) >= 8:
                return results
    if len(results) < 8:
        for item in service.trending(limit=16, display_currency=display_currency, tax_country_code=tax_country_code):
            if item['id'] in seen:
                continue
            seen.add(item['id'])
            results.append(item)
            if len(results) >= 8:
                break
    return results


class AdminShopperListCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _shopper_queryset()
        query = request.query_params.get('q', '').strip()
        list_status = request.query_params.get('status', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(customer__email__icontains=query)
                | Q(customer__first_name__icontains=query) | Q(customer__last_name__icontains=query)
            )
        if list_status:
            queryset = queryset.filter(status=list_status)
        return Response({'results': [shopper_list_payload(item, include_token=True) for item in queryset[:200]]})

    @transaction.atomic
    def post(self, request):
        serializer = ShopperListWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shopper_list = ShopperList.objects.create(
            customer_id=data['customer_id'],
            created_by=request.user,
            title=data['title'],
            note=data.get('note', ''),
            status=data.get('status', ShopperList.Status.DRAFT),
            expires_at=data.get('expires_at'),
        )
        replace_shopper_list_items(shopper_list, data['items'])
        shopper_list = get_object_or_404(_shopper_queryset(), id=shopper_list.id)
        return Response({'shopper_list': shopper_list_payload(shopper_list, include_token=True)}, status=status.HTTP_201_CREATED)


class AdminShopperListDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, list_id):
        return get_object_or_404(_shopper_queryset(), id=list_id)

    def get(self, request, list_id):
        return Response({'shopper_list': shopper_list_payload(self.get_object(list_id), include_token=True)})

    @transaction.atomic
    def patch(self, request, list_id):
        shopper_list = self.get_object(list_id)
        initial = {
            'customer_id': shopper_list.customer_id,
            'title': shopper_list.title,
            'note': shopper_list.note,
            'status': shopper_list.status,
            'expires_at': shopper_list.expires_at,
            'items': [{'product_id': item.product_id, 'quantity': item.quantity, 'note': item.note} for item in shopper_list.items.all()],
        }
        initial.update(request.data)
        serializer = ShopperListWriteSerializer(data=initial)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shopper_list.customer_id = data['customer_id']
        shopper_list.title = data['title']
        shopper_list.note = data.get('note', '')
        shopper_list.status = data['status']
        shopper_list.expires_at = data.get('expires_at')
        shopper_list.save()
        replace_shopper_list_items(shopper_list, data['items'])
        return Response({'shopper_list': shopper_list_payload(self.get_object(list_id), include_token=True)})

    def delete(self, request, list_id):
        shopper_list = self.get_object(list_id)
        shopper_list.status = ShopperList.Status.ARCHIVED
        shopper_list.save(update_fields=['status', 'date_updated'])
        return Response({'shopper_list': shopper_list_payload(shopper_list, include_token=True)})


class ShopperListCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = _shopper_queryset().filter(customer=request.user).exclude(status=ShopperList.Status.DRAFT)
        display_currency = resolve_display_currency(request)
        tax_country_code = resolve_tax_country(request)
        return Response(
            {
                'results': [
                    shopper_list_payload(
                        item,
                        display_currency,
                        include_tax=True,
                        tax_country_code=tax_country_code,
                    )
                    for item in queryset
                ]
            }
        )


class ShopperHubAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, token):
        shopper_list = get_object_or_404(_shopper_queryset(), share_token=token)
        if shopper_list.customer_id != request.user.id:
            self.permission_denied(request, message='This personal shopper list belongs to another customer.')
        if shopper_list.status in {ShopperList.Status.DRAFT, ShopperList.Status.ARCHIVED}:
            raise serializers.ValidationError('This personal shopper list is not available.')
        if shopper_list.expires_at and shopper_list.expires_at <= timezone.now():
            raise serializers.ValidationError('This personal shopper list has expired.')
        return shopper_list

    def get(self, request, token):
        shopper_list = self.get_object(request, token)
        if shopper_list.status == ShopperList.Status.SHARED:
            shopper_list.status = ShopperList.Status.VIEWED
            shopper_list.viewed_at = timezone.now()
            shopper_list.save(update_fields=['status', 'viewed_at', 'date_updated'])
        display_currency = resolve_display_currency(request)
        tax_country_code = resolve_tax_country(request)
        return Response({
            'shopper_list': shopper_list_payload(
                shopper_list,
                display_currency,
                include_tax=True,
                tax_country_code=tax_country_code,
            ),
            'recommendations': _recommendations(shopper_list, display_currency, tax_country_code),
        })


class ShopperHubAddedToCartAPIView(ShopperHubAPIView):
    def post(self, request, token):
        shopper_list = self.get_object(request, token)
        shopper_list.status = ShopperList.Status.ADDED_TO_CART
        shopper_list.added_to_cart_at = timezone.now()
        shopper_list.save(update_fields=['status', 'added_to_cart_at', 'date_updated'])
        return Response({'detail': 'Personal shopper list marked as added to cart.'})
