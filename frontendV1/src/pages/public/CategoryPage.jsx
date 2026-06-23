import { useEffect, useMemo } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import ProductSortBar from "../../components/catalog/ProductSortBar.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { useCategories } from "../../hooks/useCategories";
import { useProducts } from "../../hooks/useProducts";

export default function CategoryPage() {
  const { categorySlug = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { categories, error: categoriesError } = useCategories();
  const { products, pagination, loading, error, fetchProducts } = useProducts({}, { auto: false });

  const params = useMemo(() => ({
    category: categorySlug,
    in_stock: searchParams.get("in_stock") === "true" || undefined,
    min_price: searchParams.get("min_price") || undefined,
    max_price: searchParams.get("max_price") || undefined,
    sort_by: searchParams.get("sort_by") || "relevance",
    page: Number(searchParams.get("page") || 1),
    page_size: 24
  }), [categorySlug, searchParams]);

  const category = useMemo(
    () => categories.find((item) => item.slug === categorySlug),
    [categories, categorySlug]
  );

  useEffect(() => {
    void fetchProducts(params);
  }, [fetchProducts, params]);

  function setCategoryParams(nextValues) {
    const next = new URLSearchParams(searchParams);
    Object.entries(nextValues).forEach(([key, value]) => {
      if (value === "" || value === false || value === undefined || value === null) next.delete(key);
      else next.set(key, String(value));
    });
    next.delete("page");
    setSearchParams(next);
  }

  function changePage(nextPage) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <section className="category-page">
      <Link className="back-link" to="/catalog">
        <MaterialIcon name="arrow_back" size={18} />
        All products
      </Link>

      <div className="category-page__head surface-panel">
        <div>
          <h1>{category?.name || titleFromSlug(categorySlug)}</h1>
          <p>{pagination?.total || 0} product{pagination?.total === 1 ? "" : "s"}</p>
        </div>
        {products.length ? (
          <ProductSortBar
            total={pagination?.total || 0}
            page={pagination?.page || params.page}
            numPages={pagination?.num_pages || 1}
            sortBy={params.sort_by}
            onSortChange={(sort_by) => setCategoryParams({ sort_by })}
            compact
            hideSummary
          />
        ) : null}
      </div>

      <Alert>{categoriesError || error}</Alert>

      <ProductGrid
        products={products}
        loading={loading}
        skeletonCount={12}
        emptyTitle="No products in this category"
        emptyMessage="Choose another category or use search."
      />
      <Pagination
        page={pagination?.page || params.page}
        numPages={pagination?.num_pages || 1}
        onPageChange={changePage}
      />
    </section>
  );
}

function titleFromSlug(slug) {
  return String(slug || "Category")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
