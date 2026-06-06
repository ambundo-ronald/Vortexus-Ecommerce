import { useEffect, useMemo } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import ProductSortBar from "../../components/catalog/ProductSortBar.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { useProducts } from "../../hooks/useProducts";
import { useSearchFacets } from "../../hooks/useSearchFacets";

export default function BrandPage() {
  const { brandSlug = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { facets, error: facetsError } = useSearchFacets();
  const { products, pagination, loading, error, fetchProducts } = useProducts({}, { auto: false });

  const brand = useMemo(
    () => facets.brands.find((item) => (item.slug || item.name) === brandSlug),
    [brandSlug, facets.brands]
  );

  const params = useMemo(() => ({
    brand: brandSlug,
    category: searchParams.get("category") || "",
    in_stock: searchParams.get("in_stock") === "true" || undefined,
    min_price: searchParams.get("min_price") || undefined,
    max_price: searchParams.get("max_price") || undefined,
    sort_by: searchParams.get("sort_by") || "relevance",
    page: Number(searchParams.get("page") || 1),
    page_size: 24
  }), [brandSlug, searchParams]);

  useEffect(() => {
    void fetchProducts(params);
  }, [fetchProducts, params]);

  function setBrandParams(nextValues) {
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
        <span>Brand</span>
        <h1>{brand?.name || titleFromSlug(brandSlug)}</h1>
        <p>{pagination?.total || 0} product{pagination?.total === 1 ? "" : "s"}</p>
      </div>

      <Alert>{facetsError || error}</Alert>

      <ProductSortBar
        total={pagination?.total || 0}
        page={pagination?.page || params.page}
        numPages={pagination?.num_pages || 1}
        sortBy={params.sort_by}
        onSortChange={(sort_by) => setBrandParams({ sort_by })}
      />
      <ProductGrid products={products} loading={loading} skeletonCount={12} />
      <Pagination
        page={pagination?.page || params.page}
        numPages={pagination?.num_pages || 1}
        onPageChange={changePage}
      />
    </section>
  );
}

function titleFromSlug(slug) {
  return String(slug || "Brand")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
