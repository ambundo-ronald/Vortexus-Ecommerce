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
  const {
    reviews,
    summary,
    yourReview,
    reviewEligibility,
    loading,
    saving,
    error,
    createReview,
    voteReview
  } = useProductReviews(productId);
  const [visibleCount, setVisibleCount] = useState(2);
  const visibleReviews = useMemo(() => reviews.slice(0, visibleCount), [reviews, visibleCount]);
  const reviewCount = Number(summary?.review_count || reviews.length || 0);
  const verifiedCount = Number(summary?.verified_rating_count || 0);
  const average = verifiedCount > 0 ? Number(summary?.average_score || 0) : 0;
  const distribution = useMemo(() => {
    const rows = summary?.rating_distribution || [];
    const byScore = new Map(rows.map((row) => [Number(row.score), Number(row.count || 0)]));
    return [5, 4, 3, 2, 1].map((score) => ({
      score,
      count: byScore.get(score) || 0,
      percentage: verifiedCount ? ((byScore.get(score) || 0) / verifiedCount) * 100 : 0
    }));
  }, [summary?.rating_distribution, verifiedCount]);
  const hasMoreReviews = visibleReviews.length < reviews.length;

  return (
    <section className="content-section reviews-section">
      <div className="customer-feedback__heading">
        <h2>Customer Feedback</h2>
        {reviews.length > 2 ? (
          <button
            className="customer-feedback__see-all"
            type="button"
            onClick={() => setVisibleCount(hasMoreReviews ? reviews.length : 2)}
          >
            {hasMoreReviews ? "See All" : "Show Less"}
            <MaterialIcon name={hasMoreReviews ? "chevron_right" : "expand_less"} size={20} />
          </button>
        ) : null}
      </div>

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading reviews" /> : null}

      <div className="customer-feedback__layout">
        <aside className="rating-overview" aria-label="Verified rating summary">
          <h3>Verified Ratings ({verifiedCount})</h3>
          <div className="rating-overview__score">
            <strong>{Number(average || 0).toFixed(1)}<span>/5</span></strong>
            <StarRating value={average} size={24} />
            <p>{verifiedCount} verified rating{verifiedCount === 1 ? "" : "s"}</p>
          </div>
          <div className="rating-overview__distribution">
            {distribution.map((row) => (
              <div className="rating-distribution-row" key={row.score}>
                <span>{row.score}</span>
                <MaterialIcon name="star" size={18} filled />
                <span className="rating-distribution-row__count">({row.count})</span>
                <span className="rating-distribution-row__track" aria-hidden="true">
                  <span style={{ width: `${row.percentage}%` }} />
                </span>
              </div>
            ))}
          </div>
        </aside>

        <div className="review-list-panel">
          <h3>Product Reviews ({reviewCount})</h3>
          {!loading && !reviews.length ? (
            <div className="empty-state customer-feedback__empty">
              <strong>No product reviews yet</strong>
              <p>Verified buyers can be the first to review this product.</p>
            </div>
          ) : null}
          {reviews.length ? (
            <div className="review-grid">
              {visibleReviews.map((review) => (
                <ReviewCard
                  key={review.id}
                  review={review}
                  saving={saving}
                  onVote={(reviewId, delta) => voteReview(reviewId, delta)}
                />
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="review-action-panel">
        {user && yourReview ? (
          <Alert tone="warning">Your review is saved as {yourReview.status_label}. You can manage it from your account.</Alert>
        ) : user && reviewEligibility?.eligible ? (
          <ReviewForm saving={saving} onSubmit={createReview} />
        ) : user ? (
          <div className="review-eligibility-message">
            <MaterialIcon name="verified_user" size={24} />
            <div>
              <strong>Reviews are for verified buyers</strong>
              <p>{reviewEligibility?.reason || "Purchase this product using this account before leaving a review."}</p>
            </div>
          </div>
        ) : (
          <Link className="secondary-button review-login-action" to="/login" state={{ from: location }}>
            <MaterialIcon name="login" size={18} />
            Sign in with your purchasing account to review
          </Link>
        )}
      </div>
    </section>
  );
}
