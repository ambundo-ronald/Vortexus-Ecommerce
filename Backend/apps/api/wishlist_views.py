from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.currency import resolve_display_currency

from .wishlist_serializers import (
    WishListAddItemSerializer,
    WishListBulkStatusQuerySerializer,
    WishListCreateSerializer,
    WishListUpdateSerializer,
    get_default_wishlist,
    user_wishlist_queryset,
    wishlist_detail_payload,
    wishlist_summary_payload,
)


class WishListCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlists = list(user_wishlist_queryset(request.user))
        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        return Response(
            {
                'results': [
                    wishlist_summary_payload(wishlist, default_wishlist_id=default_wishlist_id)
                    for wishlist in wishlists
                ]
            }
        )

    def post(self, request):
        serializer = WishListCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        wishlist = serializer.save()
        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        return Response(
            {'wishlist': wishlist_summary_payload(wishlist, default_wishlist_id=default_wishlist_id)},
            status=status.HTTP_201_CREATED,
        )


class DefaultWishListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist = get_default_wishlist(request.user, create=True)
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist.id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=wishlist.id,
                    display_currency=resolve_display_currency(request),
                )
            }
        )


class WishListDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, wishlist_id):
        return get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)

    def get(self, request, wishlist_id: int):
        wishlist = self.get_object(request, wishlist_id)
        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=default_wishlist_id,
                    display_currency=resolve_display_currency(request),
                )
            }
        )

    def patch(self, request, wishlist_id: int):
        wishlist = self.get_object(request, wishlist_id)
        serializer = WishListUpdateSerializer(instance=wishlist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        wishlist = serializer.save()
        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        wishlist = self.get_object(request, wishlist.id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=default_wishlist_id,
                    display_currency=resolve_display_currency(request),
                )
            }
        )

    def delete(self, request, wishlist_id: int):
        wishlist = self.get_object(request, wishlist_id)
        wishlist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishListItemCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, wishlist_id: int):
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        serializer = WishListAddItemSerializer(
            data=request.data,
            context={
                'request': request,
                'wishlist': wishlist,
            },
        )
        serializer.is_valid(raise_exception=True)
        line = serializer.save()

        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=default_wishlist_id,
                    display_currency=resolve_display_currency(request),
                ),
                'item_id': line.id,
            },
            status=status.HTTP_201_CREATED,
        )


class DefaultWishListItemCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        wishlist = get_default_wishlist(request.user, create=True)
        serializer = WishListAddItemSerializer(
            data=request.data,
            context={
                'request': request,
                'wishlist': wishlist,
            },
        )
        serializer.is_valid(raise_exception=True)
        line = serializer.save()
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist.id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=wishlist.id,
                    display_currency=resolve_display_currency(request),
                ),
                'item_id': line.id,
            },
            status=status.HTTP_201_CREATED,
        )


class WishListItemDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, wishlist_id: int, product_id: int):
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        line = get_object_or_404(wishlist.lines.all(), product_id=product_id)
        line.delete()

        default_wishlist = get_default_wishlist(request.user, create=False)
        default_wishlist_id = default_wishlist.id if default_wishlist else None
        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist_id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=default_wishlist_id,
                    display_currency=resolve_display_currency(request),
                )
            }
        )


class DefaultWishListItemDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id: int):
        wishlist = get_default_wishlist(request.user, create=False)
        if wishlist is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        line = wishlist.lines.filter(product_id=product_id).first()
        if line is not None:
            line.delete()

        wishlist = get_object_or_404(user_wishlist_queryset(request.user), id=wishlist.id)
        return Response(
            {
                'wishlist': wishlist_detail_payload(
                    wishlist,
                    default_wishlist_id=wishlist.id,
                    display_currency=resolve_display_currency(request),
                )
            }
        )


class WishListItemStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WishListBulkStatusQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_ids = serializer.validated_data['product_ids']

        default_wishlist = get_default_wishlist(request.user, create=False)
        wished_product_ids = set()
        if default_wishlist is not None:
            wished_product_ids = set(
                default_wishlist.lines.filter(product_id__in=product_ids).values_list('product_id', flat=True)
            )

        return Response(
            {
                'results': [
                    {
                        'product_id': product_id,
                        'in_wishlist': product_id in wished_product_ids,
                    }
                    for product_id in product_ids
                ]
            }
        )
