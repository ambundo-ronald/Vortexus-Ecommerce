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
  const { reviews, summary, yourReview, loading, saving, error, createReview } = useProductReviews(productId);
  const average = summary?.average_score || summary?.product_rating || 0;

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

      {!loading && !reviews.length ? (
        <div className="empty-state">
          <strong>No reviews yet</strong>
          <p>Be the first to review this product.</p>
        </div>
      ) : null}

      {reviews.length ? (
        <div className="review-grid">
          {reviews.map((review) => <ReviewCard key={review.id} review={review} />)}
        </div>
      ) : null}

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
    </section>
  );
}
