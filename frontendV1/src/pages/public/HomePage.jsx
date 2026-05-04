import { Link } from "react-router-dom";

import HeroImageCarousel from "../../components/home/HeroImageCarousel.jsx";
import ProductCarousel from "../../components/catalog/ProductCarousel.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import Alert from "../../components/ui/Alert.jsx";
import { useProducts } from "../../hooks/useProducts";
import { useRecommendations } from "../../hooks/useRecommendations";

export default function HomePage() {
  const {
    recommendations,
    loading: recommendationsLoading,
    error: recommendationsError
  } = useRecommendations({ limit: 8 });
  const { products: inStockProducts, loading: inStockLoading, error: inStockError } = useProducts({
    in_stock: true,
    sort_by: "title_asc",
    page_size: 8
  });
  const { products: newestProducts, loading: newestLoading, error: newestError } = useProducts({
    sort_by: "newest",
    page_size: 8
  });

  return (
    <>
      <HeroImageCarousel />

      <ProductCarousel products={recommendations} loading={recommendationsLoading} />

      <section className="content-section">
        <div className="section-heading">
          <h2>In stock now</h2>
          <Link to="/catalog">View all</Link>
        </div>
        <Alert>{inStockError}</Alert>
        <ProductGrid products={inStockProducts} loading={inStockLoading} skeletonCount={8} emptyTitle="No in-stock products found" />
      </section>

      <section className="content-section">
        <div className="section-heading">
          <h2>New arrivals</h2>
          <Link to="/catalog?sort_by=newest">View all</Link>
        </div>
        <Alert>{newestError || recommendationsError}</Alert>
        <ProductGrid products={newestProducts.length ? newestProducts : recommendations} loading={newestLoading || recommendationsLoading} skeletonCount={8} />
      </section>
    </>
  );
}
