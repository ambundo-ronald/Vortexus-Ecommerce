export default function EmptyState({ title = "Nothing here yet", message = "Try changing your filters or searching again." }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}
