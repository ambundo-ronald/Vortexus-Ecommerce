import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import ProductFilters from "../../components/catalog/ProductFilters.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import ProductSortBar from "../../components/catalog/ProductSortBar.jsx";
import SearchBar from "../../components/search/SearchBar.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { useCategories } from "../../hooks/useCategories";
import { useSearch } from "../../hooks/useSearch";

export default function SearchPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const { categories } = useCategories();
  const query = searchParams.get("q") || "";
  const imageMode = searchParams.get("image") === "1";
  const imagePayload = location.state?.imagePayload;
  const imageName = location.state?.imageName || "";
  const imageError = location.state?.imageError || "";
  const { results, pagination, loading, error, search, setSearchResults } = useSearch();

  const params = useMemo(() => ({
    q: query,
    category: searchParams.get("category") || "",
    in_stock: searchParams.get("in_stock") === "true" || undefined,
    min_price: searchParams.get("min_price") || undefined,
    max_price: searchParams.get("max_price") || undefined,
    sort_by: searchParams.get("sort_by") || "relevance",
    page: Number(searchParams.get("page") || 1),
    page_size: 24
  }), [query, searchParams]);

  const displayFilters = useMemo(() => ({
    category: params.category,
    in_stock: Boolean(params.in_stock),
    min_price: searchParams.get("min_price") || "",
    max_price: searchParams.get("max_price") || ""
  }), [params.category, params.in_stock, searchParams]);

  useEffect(() => {
    if (imageMode && imagePayload) {
      setSearchResults({
        ...imagePayload,
        pagination: {
          page: 1,
          page_size: imagePayload.results?.length || 0,
          total: imagePayload.results?.length || 0,
          num_pages: 1,
          has_next: false
        }
      });
      return;
    }
    if (!imageMode) void search(params);
  }, [imageMode, imagePayload, params, search, setSearchResults]);

  useEffect(() => {
    if (!query.trim()) return;
    const key = "vortexus:recentSearches";
    const existing = JSON.parse(localStorage.getItem(key) || "[]");
    const next = [query.trim(), ...existing.filter((item) => item !== query.trim())].slice(0, 6);
    localStorage.setItem(key, JSON.stringify(next));
  }, [query]);

  const recentSearches = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("vortexus:recentSearches") || "[]");
    } catch {
      return [];
    }
  }, [query]);

  function setSearchValues(nextValues) {
    const next = new URLSearchParams(searchParams);
    Object.entries(nextValues).forEach(([key, value]) => {
      if (value === "" || value === false || value === undefined || value === null) next.delete(key);
      else next.set(key, String(value));
    });
    next.delete("page");
    next.delete("image");
    setSearchParams(next);
    setFiltersOpen(false);
  }

  function clearFilters() {
    const next = new URLSearchParams(searchParams);
    ["category", "in_stock", "min_price", "max_price", "page"].forEach((key) => next.delete(key));
    setSearchParams(next);
    setFiltersOpen(false);
  }

  function changePage(nextPage) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const total = pagination?.total || results.length || 0;

  return (
    <>
      <section className="surface-panel search-hero">
        <div>
          <p className="eyebrow">Search</p>
          <h1>{imageMode ? "Image search results" : query ? `Results for "${query}"` : "Find products faster"}</h1>
          <p>{imageMode && imageName ? imageName : `${total} result${total === 1 ? "" : "s"}`}</p>
        </div>
        <SearchBar initialValue={query} compact />
      </section>

      {!query && !imageMode && recentSearches.length ? (
        <section className="search-chip-section">
          <strong>Recent searches</strong>
          <div className="search-chips">
            {recentSearches.map((item) => <Link className="category-chip" to={`/search?q=${encodeURIComponent(item)}`} key={item}>{item}</Link>)}
          </div>
        </section>
      ) : null}

      <section className="search-results-shell">
        <div className="search-results-toolbar">
          <button className="secondary-button filter-drawer-trigger" type="button" onClick={() => setFiltersOpen(true)}>
            <MaterialIcon name="tune" size={18} />
            Filters
          </button>
          {!imageMode ? (
            <ProductSortBar
              total={total}
              page={pagination?.page || params.page}
              numPages={pagination?.num_pages || 1}
              sortBy={params.sort_by}
              onSortChange={(sort_by) => setSearchValues({ sort_by })}
              compact
            />
          ) : (
            <div>
              <strong>{total} products</strong>
              <span>Similar products</span>
            </div>
          )}
        </div>

        <Alert>{imageError || error}</Alert>
        {loading ? <ProductGrid products={[]} loading skeletonCount={12} /> : <ProductGrid products={results} emptyTitle="No search results" />}
        {!imageMode ? (
          <Pagination
            page={pagination?.page || params.page}
            numPages={pagination?.num_pages || 1}
            onPageChange={changePage}
          />
        ) : null}
      </section>

      <div className={`filter-drawer ${filtersOpen ? "open" : ""}`} aria-hidden={!filtersOpen}>
        <button className="filter-drawer__shade" type="button" onClick={() => setFiltersOpen(false)} aria-label="Close filters" />
        <div className="filter-drawer__panel">
          <div className="filter-drawer__head">
            <strong>Filters</strong>
            <button type="button" onClick={() => setFiltersOpen(false)} aria-label="Close filters">
              <MaterialIcon name="close" size={22} />
            </button>
          </div>
          <ProductFilters
            filters={displayFilters}
            categories={categories}
            onApply={setSearchValues}
            onClear={clearFilters}
          />
        </div>
      </div>
    </>
  );
}
