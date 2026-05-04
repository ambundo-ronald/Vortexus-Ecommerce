import EmptyState from "../ui/EmptyState.jsx";

export default function ProductSpecifications({ specifications = [] }) {
  if (!specifications.length) {
    return <EmptyState title="No technical specs yet" message="Specifications will appear here when available." />;
  }

  return (
    <dl className="spec-list">
      {specifications.map((spec) => (
        <div key={spec.code || spec.name} className="spec-row">
          <dt>{spec.name}</dt>
          <dd>{spec.value}</dd>
        </div>
      ))}
    </dl>
  );
}
