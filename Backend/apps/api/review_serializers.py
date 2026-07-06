from django.apps import apps
from django.db.models import Avg, Count
from rest_framework import serializers

INELIGIBLE_ORDER_STATUSES = ['Failed', 'Cancelled', 'Canceled', 'Refunded']


def get_product_model():
    return apps.get_model('catalogue', 'Product')


def get_review_model():
    return apps.get_model('reviews', 'ProductReview')


def moderation_review_status() -> int:
    return get_review_model().FOR_MODERATION


def get_order_line_model():
    return apps.get_model('order', 'Line')


def public_product_queryset():
    Product = get_product_model()
    return Product.objects.filter(is_public=True).exclude(structure='parent')


def review_status_label(review) -> str:
    return review.get_status_display() if hasattr(review, 'get_status_display') else str(review.status)


def user_has_purchased_product(user, product) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return (
        get_order_line_model()
        .objects.filter(product=product, order__user=user)
        .exclude(order__status__in=INELIGIBLE_ORDER_STATUSES)
        .exists()
    )


def verified_reviewer_ids_for_product(product) -> set[int]:
    return set(
        get_order_line_model()
        .objects.filter(product=product, order__user_id__isnull=False)
        .exclude(order__status__in=INELIGIBLE_ORDER_STATUSES)
        .values_list('order__user_id', flat=True)
        .distinct()
    )


def review_eligibility_for_user(user, product) -> dict:
    if not user or not getattr(user, 'is_authenticated', False):
        return {
            'eligible': False,
            'has_purchased': False,
            'has_reviewed': False,
            'reason': 'Sign in with the account used to purchase this product.',
        }

    has_reviewed = get_review_model().objects.filter(product=product, user=user).exists()
    has_purchased = user_has_purchased_product(user, product)
    if has_reviewed:
        reason = 'You have already reviewed this product.'
    elif not has_purchased:
        reason = 'Only customers who purchased this product can leave a review.'
    else:
        reason = ''
    return {
        'eligible': has_purchased and not has_reviewed,
        'has_purchased': has_purchased,
        'has_reviewed': has_reviewed,
        'reason': reason,
    }


def review_payload(review, request_user=None, verified_purchase=None) -> dict:
    reviewer_name = review.reviewer_name
    if review.user and str(reviewer_name).strip().lower() == 'anonymous':
        reviewer_name = review.user.username
    is_owner = bool(request_user and review.user_id and request_user.id == review.user_id)
    user_vote = None
    can_vote = False
    if request_user and getattr(request_user, 'is_authenticated', False):
        existing_vote = review.votes.filter(user=request_user).first()
        user_vote = existing_vote.delta if existing_vote else None
        can_vote = not is_owner and existing_vote is None
    if verified_purchase is None:
        verified_purchase = bool(
            review.user_id
            and review.product_id
            and user_has_purchased_product(review.user, review.product)
        )
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
        'up_votes': review.num_up_votes,
        'down_votes': review.num_down_votes,
        'user_vote': user_vote,
        'can_vote': can_vote,
        'date_created': review.date_created,
        'can_edit': is_owner,
        'can_delete': is_owner,
        'verified_purchase': bool(verified_purchase),
    }


def review_summary_for_product(product) -> dict:
    Review = get_review_model()
    approved_reviews = Review.objects.filter(product=product, status=Review.APPROVED)
    review_count = approved_reviews.count()
    verified_reviewer_ids = verified_reviewer_ids_for_product(product)
    verified_reviews = approved_reviews.filter(user_id__in=verified_reviewer_ids)
    stats = verified_reviews.aggregate(
        average_score=Avg('score'),
    )
    score_counts = {
        int(row['score']): row['count']
        for row in verified_reviews.values('score').annotate(count=Count('id'))
    }
    verified_count = verified_reviews.count()
    average_score = stats['average_score']
    return {
        'average_score': float(average_score) if average_score is not None else None,
        'review_count': review_count,
        'verified_rating_count': verified_count,
        'rating_distribution': [
            {'score': score, 'count': score_counts.get(score, 0)}
            for score in range(5, 0, -1)
        ],
        'product_rating': float(product.rating) if getattr(product, 'rating', None) is not None else None,
    }


class ProductReviewCreateSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=5)
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
        if not user_has_purchased_product(request.user, product):
            raise serializers.ValidationError(
                {'product': 'Only customers who purchased this product can leave a review.'}
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
            status=Review.FOR_MODERATION,
        )
        review.full_clean()
        review.save()
        return review


class ProductReviewUpdateSerializer(serializers.Serializer):
    score = serializers.IntegerField(required=False, min_value=1, max_value=5)
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

        moderation_status = moderation_review_status()
        if instance.status != moderation_status:
            instance.status = moderation_status
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
