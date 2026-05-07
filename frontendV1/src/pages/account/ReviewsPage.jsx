import { Link } from "react-router-dom";

import ReviewCard from "../../components/reviews/ReviewCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAccountReviews } from "../../hooks/useReviews";

export default function ReviewsPage() {
  const { reviews, loading, saving, error, removeReview } = useAccountReviews();

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>
      <div className="account-section-title">
        <h1>Reviews</h1>
        <p>{reviews.length} review{reviews.length === 1 ? "" : "s"}</p>
      </div>
      <Alert>{error}</Alert>
      {loading ? (
        <Spinner label="Loading reviews" />
      ) : reviews.length ? (
        <div className="review-grid">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} account saving={saving} onDelete={removeReview} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <strong>No reviews yet</strong>
          <p>Your product reviews will appear here.</p>
          <Link className="primary-button empty-state__action" to="/catalog">
            <MaterialIcon name="storefront" size={18} />
            Browse products
          </Link>
        </div>
      )}
    </section>
  );
}
