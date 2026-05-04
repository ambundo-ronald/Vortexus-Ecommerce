import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function StarRating({ value = 0, interactive = false, onChange, size = 20 }) {
  const rounded = Math.round(Number(value) || 0);

  return (
    <span className={`star-rating ${interactive ? "interactive" : ""}`}>
      {[1, 2, 3, 4, 5].map((score) => {
        const filled = score <= rounded;
        if (!interactive) {
          return <span key={score} className={filled ? "active" : ""}><MaterialIcon name="star" size={size} filled={filled} /></span>;
        }
        return (
          <button type="button" key={score} className={filled ? "active" : ""} onClick={() => onChange?.(score)} aria-label={`${score} stars`}>
            <MaterialIcon name={filled ? "star" : "star_border"} size={size} filled={filled} />
          </button>
        );
      })}
    </span>
  );
}
