export default function ProductSkeletonGrid({ count = 8 }) {
  return (
    <div className="product-grid" aria-label="Loading products">
      {Array.from({ length: count }).map((_, index) => (
        <div className="product-card product-card--skeleton" key={index}>
          <div className="product-card__media skeleton-block" />
          <div className="product-card__body">
            <span className="skeleton-line skeleton-line--short" />
            <span className="skeleton-line" />
            <span className="skeleton-line skeleton-line--medium" />
            <div className="product-card__foot">
              <span className="skeleton-line skeleton-line--price" />
              <span className="skeleton-pill" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
