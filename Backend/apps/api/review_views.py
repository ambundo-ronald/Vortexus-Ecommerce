from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .review_serializers import (
    AccountReviewListQuerySerializer,
    ProductReviewCreateSerializer,
    ProductReviewUpdateSerializer,
    filter_reviews_for_status,
    get_review_model,
    public_product_queryset,
    review_payload,
    review_summary_for_product,
)


class ProductReviewCollectionAPIView(APIView):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_product(self, product_id: int):
        return get_object_or_404(public_product_queryset(), id=product_id)

    def get(self, request, product_id: int):
        product = self.get_product(product_id)
        Review = get_review_model()

        reviews = (
            Review.objects.filter(product=product, status=Review.APPROVED)
            .select_related('user', 'product')
            .order_by('-date_created', '-id')
        )
        payload = {
            'summary': review_summary_for_product(product),
            'results': [review_payload(review, request_user=request.user) for review in reviews],
        }

        if request.user.is_authenticated:
            own_review = (
                Review.objects.filter(product=product, user=request.user)
                .select_related('user', 'product')
                .first()
            )
            payload['your_review'] = review_payload(own_review, request_user=request.user) if own_review else None

        return Response(payload)

    def post(self, request, product_id: int):
        product = self.get_product(product_id)
        serializer = ProductReviewCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'product': product,
            },
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        review = get_object_or_404(
            get_review_model().objects.select_related('user', 'product'),
            id=review.id,
        )
        return Response(
            {
                'review': review_payload(review, request_user=request.user),
                'summary': review_summary_for_product(product),
            },
            status=status.HTTP_201_CREATED,
        )


class AccountReviewCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = AccountReviewListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        status_filter = serializer.validated_data.get('status')

        queryset = (
            get_review_model()
            .objects.filter(user=request.user)
            .select_related('user', 'product')
            .order_by('-date_created', '-id')
        )
        queryset = filter_reviews_for_status(queryset, status_filter)

        return Response(
            {
                'results': [review_payload(review, request_user=request.user) for review in queryset],
                'filters': {'status': status_filter},
            }
        )


class AccountReviewDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, review_id: int):
        return get_object_or_404(
            get_review_model().objects.select_related('user', 'product'),
            id=review_id,
            user=request.user,
        )

    def get(self, request, review_id: int):
        review = self.get_object(request, review_id)
        return Response({'review': review_payload(review, request_user=request.user)})

    def patch(self, request, review_id: int):
        review = self.get_object(request, review_id)
        serializer = ProductReviewUpdateSerializer(instance=review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        review = self.get_object(request, review.id)
        return Response(
            {
                'review': review_payload(review, request_user=request.user),
                'summary': review_summary_for_product(review.product) if review.product else None,
            }
        )

    def delete(self, request, review_id: int):
        review = self.get_object(request, review_id)
        product = review.product
        review.delete()
        payload = {'detail': 'Review deleted successfully.'}
        if product is not None:
            payload['summary'] = review_summary_for_product(product)
        return Response(payload, status=status.HTTP_200_OK)
