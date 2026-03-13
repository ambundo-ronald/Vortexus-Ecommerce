from django.apps import apps
from django.db.models import Avg, Count
from oscar.apps.catalogue.reviews.utils import get_default_review_status
from rest_framework import serializers


def get_product_model():
    return apps.get_model('catalogue', 'Product')


def get_review_model():
    return apps.get_model('reviews', 'ProductReview')


def public_product_queryset():
    Product = get_product_model()
    return Product.objects.filter(is_public=True).exclude(structure='parent')


def review_status_label(review) -> str:
    return review.get_status_display() if hasattr(review, 'get_status_display') else str(review.status)


def review_payload(review, request_user=None) -> dict:
    reviewer_name = review.reviewer_name
    if review.user and str(reviewer_name).strip().lower() == 'anonymous':
        reviewer_name = review.user.username
    is_owner = bool(request_user and review.user_id and request_user.id == review.user_id)
    return {
        'id': review.id,
        'product_id': review.product_id,
        'product_title': review.product.get_title() if review.product else review.title,
        'score': review.score,
        'title': review.title,
        'body': review.body,
        'status': review.status,
        'status_label': review_status_label(review),
        'reviewer_name': str(reviewer_name),
        'total_votes': review.total_votes,
        'delta_votes': review.delta_votes,
        'date_created': review.date_created,
        'can_edit': is_owner,
        'can_delete': is_owner,
    }


def review_summary_for_product(product) -> dict:
    Review = get_review_model()
    stats = Review.objects.filter(product=product, status=Review.APPROVED).aggregate(
        average_score=Avg('score'),
        review_count=Count('id'),
    )
    average_score = stats['average_score']
    return {
        'average_score': float(average_score) if average_score is not None else None,
        'review_count': stats['review_count'] or 0,
        'product_rating': float(product.rating) if getattr(product, 'rating', None) is not None else None,
    }


class ProductReviewCreateSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=5)
    title = serializers.CharField(max_length=255)
    body = serializers.CharField(max_length=5000)

    def validate_title(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Review title cannot be blank.')
        return cleaned

    def validate_body(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Review body cannot be blank.')
        return cleaned

    def validate(self, attrs):
        request = self.context['request']
        product = self.context['product']
        Review = get_review_model()

        if Review.objects.filter(product=product, user=request.user).exists():
            raise serializers.ValidationError(
                {'product': 'You have already reviewed this product. Update your existing review instead.'}
            )
        return attrs

    def create(self, validated_data):
        Review = get_review_model()
        request = self.context['request']
        product = self.context['product']

        review = Review(
            product=product,
            user=request.user,
            score=validated_data['score'],
            title=validated_data['title'],
            body=validated_data['body'],
            status=get_default_review_status(),
        )
        review.full_clean()
        review.save()
        return review


class ProductReviewUpdateSerializer(serializers.Serializer):
    score = serializers.IntegerField(required=False, min_value=0, max_value=5)
    title = serializers.CharField(required=False, max_length=255)
    body = serializers.CharField(required=False, max_length=5000)

    def validate_title(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Review title cannot be blank.')
        return cleaned

    def validate_body(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Review body cannot be blank.')
        return cleaned

    def update(self, instance, validated_data):
        dirty_fields = []
        for field in ('score', 'title', 'body'):
            if field in validated_data and getattr(instance, field) != validated_data[field]:
                setattr(instance, field, validated_data[field])
                dirty_fields.append(field)

        default_status = get_default_review_status()
        if instance.status != default_status:
            instance.status = default_status
            dirty_fields.append('status')

        if dirty_fields:
            instance.full_clean()
            instance.save(update_fields=dirty_fields)
        return instance


class AccountReviewListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        required=False,
        choices=['approved', 'pending', 'rejected'],
    )


def filter_reviews_for_status(queryset, raw_status: str | None):
    Review = get_review_model()
    if raw_status == 'approved':
        return queryset.filter(status=Review.APPROVED)
    if raw_status == 'pending':
        return queryset.filter(status=Review.FOR_MODERATION)
    if raw_status == 'rejected':
        return queryset.filter(status=Review.REJECTED)
    return queryset
