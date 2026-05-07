export default function MaterialIcon({ name, size = 22, filled = false, className = "", title }) {
  return (
    <span
      className={`material-symbols-rounded ${className}`}
      aria-hidden={title ? undefined : "true"}
      title={title}
      style={{
        fontSize: size,
        fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 500, 'GRAD' 0, 'opsz' ${size}`
      }}
    >
      {name}
    </span>
  );
}
