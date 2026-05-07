import { useEffect, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function ProductFilters({ filters, categories = [], onApply, onClear }) {
  const [draft, setDraft] = useState(filters);

  useEffect(() => {
    setDraft(filters);
  }, [filters]);

  function updateField(field, value) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onApply({
      category: draft.category || "",
      in_stock: Boolean(draft.in_stock),
      min_price: draft.min_price || "",
      max_price: draft.max_price || ""
    });
  }

  return (
    <form className="catalog-filters" onSubmit={submit}>
      <div className="catalog-filters__title">
        <MaterialIcon name="tune" size={18} />
        <strong>Filters</strong>
      </div>

      <label className="field-control">
        <span>Category</span>
        <select value={draft.category || ""} onChange={(event) => updateField("category", event.target.value)}>
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.slug}>
              {category.name}
            </option>
          ))}
        </select>
      </label>

      <label className="toggle-control">
        <input
          type="checkbox"
          checked={Boolean(draft.in_stock)}
          onChange={(event) => updateField("in_stock", event.target.checked)}
        />
        <span>In stock only</span>
      </label>

      <div className="price-fields">
        <label className="field-control">
          <span>Min price</span>
          <input
            inputMode="decimal"
            min="0"
            type="number"
            value={draft.min_price || ""}
            onChange={(event) => updateField("min_price", event.target.value)}
          />
        </label>
        <label className="field-control">
          <span>Max price</span>
          <input
            inputMode="decimal"
            min="0"
            type="number"
            value={draft.max_price || ""}
            onChange={(event) => updateField("max_price", event.target.value)}
          />
        </label>
      </div>

      <div className="filter-actions">
        <button className="primary-button" type="submit">
          Apply
        </button>
        <button className="secondary-button" type="button" onClick={onClear}>
          <MaterialIcon name="close" size={17} />
          Clear
        </button>
      </div>
    </form>
  );
}
