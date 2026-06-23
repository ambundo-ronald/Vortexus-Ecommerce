import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function StarRating({ value = 0, interactive = false, onChange, size = 20 }) {
  const numericValue = Math.max(0, Math.min(5, Number(value) || 0));
  const rounded = Math.round(numericValue);

  return (
    <span
      className={`star-rating ${interactive ? "interactive" : ""}`}
      aria-label={`${numericValue.toFixed(1)} out of 5 stars`}
    >
      {[1, 2, 3, 4, 5].map((score) => {
        const filled = score <= rounded;
        if (!interactive) {
          return (
            <MaterialIcon
              key={score}
              name="star"
              size={size}
              filled={filled}
              className={`star-rating__star ${filled ? "is-filled" : "is-empty"}`}
            />
          );
        }
        return (
          <button type="button" key={score} className={filled ? "active" : ""} onClick={() => onChange?.(score)} aria-label={`${score} stars`}>
            <MaterialIcon
              name="star"
              size={size}
              filled={filled}
              className={`star-rating__star ${filled ? "is-filled" : "is-empty"}`}
            />
          </button>
        );
      })}
    </span>
  );
}
