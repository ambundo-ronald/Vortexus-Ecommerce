import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import ProductFilters from "../../components/catalog/ProductFilters.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import ProductSortBar from "../../components/catalog/ProductSortBar.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { useCategories } from "../../hooks/useCategories";
import { useProducts } from "../../hooks/useProducts";

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories();
  const { products, pagination, loading, error, fetchProducts } = useProducts({}, { auto: false });

  const params = useMemo(() => ({
    q: searchParams.get("q") || "",
    category: searchParams.get("category") || "",
    in_stock: searchParams.get("in_stock") === "true" || undefined,
    min_price: searchParams.get("min_price") || undefined,
    max_price: searchParams.get("max_price") || undefined,
    sort_by: searchParams.get("sort_by") || "relevance",
    page: Number(searchParams.get("page") || 1),
    page_size: 24
  }), [searchParams]);

  const displayFilters = useMemo(() => ({
    category: params.category,
    in_stock: Boolean(params.in_stock),
    min_price: searchParams.get("min_price") || "",
    max_price: searchParams.get("max_price") || ""
  }), [params.category, params.in_stock, searchParams]);

  const activeCategory = useMemo(() => {
    if (!params.category) return null;
    return categories.find((category) => category.slug === params.category) || null;
  }, [categories, params.category]);

  useEffect(() => {
    void fetchProducts(params);
  }, [fetchProducts, params]);

  function setCatalogParams(nextValues) {
    const next = new URLSearchParams(searchParams);
    Object.entries(nextValues).forEach(([key, value]) => {
      if (value === "" || value === false || value === undefined || value === null) {
        next.delete(key);
      } else {
        next.set(key, String(value));
      }
    });
    next.delete("page");
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

  return (
    <>
      <section className="catalog-page">
        <Alert>{categoriesError || error}</Alert>

        <div className="catalog-layout">
          <aside className="catalog-sidebar">
            <ProductFilters
              filters={displayFilters}
              categories={categories}
              onApply={setCatalogParams}
              onClear={clearFilters}
            />
          </aside>
          <div className="catalog-results">
            <div className="catalog-mobile-actions">
              <button className="secondary-button filter-drawer-trigger catalog-mobile-filter" type="button" onClick={() => setFiltersOpen(true)}>
                <MaterialIcon name="tune" size={18} />
                Filters
              </button>
              <span className="catalog-active-category">
                {categoriesLoading ? "Loading categories..." : activeCategory?.name || "All products"}
              </span>
            </div>
            <ProductSortBar
              total={pagination?.total || 0}
              page={pagination?.page || params.page}
              numPages={pagination?.num_pages || 1}
              sortBy={params.sort_by}
              onSortChange={(sort_by) => setCatalogParams({ sort_by })}
            />
            <ProductGrid products={products} loading={loading} skeletonCount={12} />
            <Pagination
              page={pagination?.page || params.page}
              numPages={pagination?.num_pages || 1}
              onPageChange={changePage}
            />
          </div>
        </div>
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
            onApply={setCatalogParams}
            onClear={clearFilters}
          />
        </div>
      </div>
    </>
  );
}
