import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import StarRating from "./StarRating.jsx";
import { formatDate } from "../../utils/formatDate";

export default function ReviewCard({ review, account = false, saving = false, onDelete }) {
  return (
    <article className="review-card">
      <div className="review-card__head">
        <div>
          <StarRating value={review.score} size={18} />
          <h3>{review.title}</h3>
        </div>
        <span className="review-status">{review.status_label || "Review"}</span>
      </div>
      <p>{review.body}</p>
      <div className="review-card__meta">
        <span>{review.reviewer_name || "Customer"}</span>
        <span>{formatDate(review.date_created)}</span>
      </div>
      {account ? (
        <div className="review-card__actions">
          <Link className="secondary-button" to={review.product_id ? `/products/${review.product_id}` : "/catalog"}>
            <MaterialIcon name="visibility" size={18} />
            Product
          </Link>
          <button className="danger-link review-delete" type="button" disabled={saving} onClick={() => onDelete?.(review.id)} aria-label="Delete review">
            <MaterialIcon name="delete" size={18} />
          </button>
        </div>
      ) : null}
    </article>
  );
}
