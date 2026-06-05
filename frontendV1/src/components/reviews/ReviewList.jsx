import { useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import Spinner from "../ui/Spinner.jsx";
import ReviewCard from "./ReviewCard.jsx";
import ReviewForm from "./ReviewForm.jsx";
import StarRating from "./StarRating.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useProductReviews } from "../../hooks/useReviews";

export default function ReviewList({ productId }) {
  const location = useLocation();
  const { user } = useAuth();
  const { reviews, summary, yourReview, loading, saving, error, createReview, voteReview } = useProductReviews(productId);
  const average = summary?.average_score || summary?.product_rating || 0;
  const [visibleCount, setVisibleCount] = useState(2);
  const visibleReviews = useMemo(() => reviews.slice(0, visibleCount), [reviews, visibleCount]);
  const hiddenCount = Math.max(reviews.length - visibleReviews.length, 0);
  const nextCount = Math.min(2, hiddenCount);

  return (
    <section className="content-section reviews-section">
      <div className="section-heading">
        <h2>Reviews</h2>
        <span className="review-summary-pill">
          <StarRating value={average} size={16} />
          {summary?.review_count || 0}
        </span>
      </div>

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading reviews" /> : null}

      <div className="review-list-panel">
        {!loading && !reviews.length ? (
          <div className="empty-state">
            <strong>No reviews yet</strong>
            <p>Be the first to review this product.</p>
          </div>
        ) : null}

        {reviews.length ? (
          <>
            <div className="review-grid">
              {visibleReviews.map((review) => (
                <ReviewCard key={review.id} review={review} saving={saving} onVote={(reviewId, delta) => voteReview(reviewId, delta)} />
              ))}
            </div>
            {hiddenCount ? (
              <button className="secondary-button review-more-button" type="button" onClick={() => setVisibleCount((count) => count + 2)}>
                <MaterialIcon name="expand_more" size={18} />
                Show {nextCount} more review{nextCount === 1 ? "" : "s"}
                <span>{hiddenCount} left</span>
              </button>
            ) : reviews.length > 2 ? (
              <button className="secondary-button review-more-button" type="button" onClick={() => setVisibleCount(2)}>
                <MaterialIcon name="expand_less" size={18} />
                Show first 2
              </button>
            ) : null}
          </>
        ) : null}
      </div>

      <div className="review-action-panel">
        {user && yourReview ? (
          <Alert tone="warning">Your review is saved as {yourReview.status_label}. You can manage it from your account.</Alert>
        ) : user ? (
          <ReviewForm saving={saving} onSubmit={createReview} />
        ) : (
          <Link className="secondary-button review-login-action" to="/login" state={{ from: location }}>
            <MaterialIcon name="login" size={18} />
            Sign in to review
          </Link>
        )}
      </div>
    </section>
  );
}
