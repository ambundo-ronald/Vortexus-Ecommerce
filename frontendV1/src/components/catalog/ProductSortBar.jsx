import MaterialIcon from "../ui/MaterialIcon.jsx";

const sortOptions = [
  { value: "relevance", label: "Featured" },
  { value: "newest", label: "Newest" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "title_asc", label: "Name A-Z" }
];

export default function ProductSortBar({ total = 0, page = 1, numPages = 1, sortBy = "relevance", onSortChange, compact = false }) {
  const pageLabel = numPages > 1 ? `Page ${page} of ${numPages}` : "Catalog";

  return (
    <div className={compact ? "sort-bar sort-bar--compact" : "sort-bar"}>
      <div>
        <strong>{total} products</strong>
        <span>{pageLabel}</span>
      </div>
      <label className="sort-select">
        <MaterialIcon name="swap_vert" size={18} />
        <select value={sortBy} onChange={(event) => onSortChange(event.target.value)} aria-label="Sort products">
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
