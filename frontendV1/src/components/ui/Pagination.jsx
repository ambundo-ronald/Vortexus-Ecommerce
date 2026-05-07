import MaterialIcon from "./MaterialIcon.jsx";

export default function Pagination({ page = 1, numPages = 1, onPageChange }) {
  if (!numPages || numPages <= 1) return null;

  const pages = Array.from({ length: numPages }, (_, index) => index + 1).filter(
    (pageNumber) => pageNumber === 1 || pageNumber === numPages || Math.abs(pageNumber - page) <= 1
  );

  return (
    <nav className="pagination" aria-label="Product pages">
      <button type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)} aria-label="Previous page">
        <MaterialIcon name="chevron_left" size={20} />
      </button>
      {pages.map((pageNumber, index) => {
        const previous = pages[index - 1];
        return (
          <span className="pagination__group" key={pageNumber}>
            {previous && pageNumber - previous > 1 ? <span className="pagination__ellipsis">...</span> : null}
            <button
              type="button"
              className={pageNumber === page ? "active" : ""}
              onClick={() => onPageChange(pageNumber)}
              aria-label={`Page ${pageNumber}`}
              aria-current={pageNumber === page ? "page" : undefined}
            >
              {pageNumber}
            </button>
          </span>
        );
      })}
      <button type="button" disabled={page >= numPages} onClick={() => onPageChange(page + 1)} aria-label="Next page">
        <MaterialIcon name="chevron_right" size={20} />
      </button>
    </nav>
  );
}
