import { useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import StarRating from "./StarRating.jsx";

export default function ReviewForm({ saving = false, onSubmit }) {
  const [score, setScore] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({ score, title, body });
  }

  return (
    <form className="review-form checkout-card" onSubmit={handleSubmit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name="rate_review" size={20} /></span>
        <div>
          <h2>Write a review</h2>
          <p>Share what helped you decide.</p>
        </div>
      </div>
      <label>
        <span>Rating</span>
        <StarRating value={score} interactive onChange={setScore} size={28} />
      </label>
      <label>
        <span>Title</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength="255" required />
      </label>
      <label>
        <span>Review</span>
        <textarea value={body} onChange={(event) => setBody(event.target.value)} rows="4" required />
      </label>
      <button className="primary-button checkout-submit" type="submit" disabled={saving}>
        <MaterialIcon name="send" size={18} />
        {saving ? "Submitting..." : "Submit review"}
      </button>
    </form>
  );
}
