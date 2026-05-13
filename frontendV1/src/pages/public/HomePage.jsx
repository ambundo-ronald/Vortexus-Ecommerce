import { useState } from "react";
import { Link } from "react-router-dom";

import HeroImageCarousel from "../../components/home/HeroImageCarousel.jsx";
import { AnnouncementStrip, BrandStrip, FeaturedMarketingBlocks } from "../../components/home/MarketingBlocks.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useCategories } from "../../hooks/useCategories";
import { useMarketingBlocks } from "../../hooks/useMarketingBlocks";
import { useProducts } from "../../hooks/useProducts";
import { useRecommendations } from "../../hooks/useRecommendations";
import { mediaUrl } from "../../utils/media";
import { productImageUrl } from "../../utils/productImages";
import { productInitials } from "../../utils/productDisplay";
import "./HomePage.css";

const fallbackCategories = [
  { id: "pumps", name: "Pumps & Motors", slug: "pumps-motors", icon: "settings" },
  { id: "tanks", name: "Tanks & Vessels", slug: "tanks-vessels", icon: "inventory_2" },
  { id: "valves", name: "Valves & Fittings", slug: "valves-fittings", icon: "plumbing" },
  { id: "sensors", name: "Controllers & Sensors", slug: "controllers-sensors", icon: "sensors" },
  { id: "water-treatment", name: "Water Treatment", slug: "water-treatment", icon: "water_drop" },
  { id: "pipes", name: "Pipes & Accessories", slug: "pipes-accessories", icon: "polyline" },
  { id: "power", name: "Electrical & Power", slug: "electrical-power", icon: "bolt" },
  { id: "tools", name: "Tools & Equipment", slug: "tools-equipment", icon: "construction" },
  { id: "offers", name: "Deals & Offers", slug: "", icon: "local_offer", to: "/offers" }
];

const valueProps = [
  { icon: "verified", title: "Quality products", text: "Sourced for real project use" },
  { icon: "support_agent", title: "Expert support", text: "Help from industry teams" },
  { icon: "local_shipping", title: "Fast delivery", text: "Reliable dispatch options" },
  { icon: "payments", title: "Secure checkout", text: "Safe payment choices" },
  { icon: "assignment_return", title: "Easy returns", text: "Clear account support" }
];

export default function HomePage() {
  const [categoriesCollapsed, setCategoriesCollapsed] = useState(false);
  const { blocks: marketingBlocks, loading: marketingLoading } = useMarketingBlocks();
  const { categories } = useCategories();
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

  const marketingByPlacement = marketingBlocks.reduce((groups, block) => {
    const placement = block.placement || "featured";
    return { ...groups, [placement]: [...(groups[placement] || []), block] };
  }, {});
  const categoryItems = categories.length ? categories : fallbackCategories;
  const newestPreview = newestProducts.length ? newestProducts.slice(0, 6) : recommendations.slice(0, 6);
  const firstPromo = marketingByPlacement.promo_banner?.[0];

  return (
    <div className="home-page">
      <AnnouncementStrip blocks={marketingByPlacement.announcement} />

      <section className={`home-showcase${categoriesCollapsed ? " home-showcase--categories-collapsed" : ""}`} aria-label="Store highlights">
        <aside className={`home-category-panel${categoriesCollapsed ? " is-collapsed" : ""}`}>
          <div className="home-category-panel__head">
            <strong>Browse categories</strong>
            <button
              className="home-category-panel__toggle"
              type="button"
              aria-label={categoriesCollapsed ? "Open categories" : "Collapse categories"}
              aria-expanded={!categoriesCollapsed}
              onClick={() => setCategoriesCollapsed((current) => !current)}
            >
              <MaterialIcon name={categoriesCollapsed ? "category" : "menu"} size={20} />
            </button>
          </div>
          <nav className="home-category-list" aria-label="Homepage categories">
            {categoryItems.map((category, index) => (
              <Link key={category.id || category.slug || category.name} to={category.to || categoryUrl(category)} title={category.name}>
                <MaterialIcon name={category.icon || fallbackCategories[index % fallbackCategories.length].icon} size={19} />
                <span>{category.name}</span>
                <MaterialIcon name="chevron_right" size={18} />
              </Link>
            ))}
          </nav>
          <Link className="home-help-card" to="/quote">
            <MaterialIcon name="support_agent" size={22} />
            <span>Need help finding the right product?</span>
            <strong>Contact our experts</strong>
          </Link>
        </aside>

        <div className="home-showcase__main">
          <HeroImageCarousel blocks={marketingByPlacement.home_hero} loading={marketingLoading} />
          <section className="home-arrivals-strip" aria-label="New arrivals preview">
            <div>
              <span>New arrivals</span>
              <strong>These are the newest products in the store</strong>
              <Link to="/catalog?sort_by=newest">
                Check what is new
                <MaterialIcon name="arrow_forward" size={17} />
              </Link>
            </div>
            <div className="home-arrivals-strip__items">
              {(newestLoading || recommendationsLoading) && !newestPreview.length
                ? Array.from({ length: 6 }).map((_, index) => <span className="home-product-thumb skeleton-block" key={index} />)
                : newestPreview.map((product) => <ProductThumb key={product.id} product={product} />)}
            </div>
          </section>
        </div>
      </section>

      <FeaturedMarketingBlocks blocks={marketingByPlacement.featured} />

      <section className="content-section home-product-section">
        <div className="section-heading">
          <h2>New Arrivals</h2>
          <Link to="/catalog?sort_by=newest">View all</Link>
        </div>
        <Alert>{newestError || recommendationsError}</Alert>
        <ProductGrid products={newestProducts.slice(0, 5).length ? newestProducts.slice(0, 5) : recommendations.slice(0, 5)} loading={newestLoading || recommendationsLoading} skeletonCount={5} />
      </section>

      <Link className="home-deal-banner" to={firstPromo?.cta_url || "/offers"}>
        <div>
          <span>{firstPromo?.eyebrow || "Flash sales"}</span>
          <strong>{firstPromo?.headline || "Ending in 2hrs"}</strong>
          <small>{firstPromo?.body || "Take a chance to buy within the time."}</small>
          <em>{firstPromo?.cta_text || "Shop the sale"}</em>
        </div>
        {firstPromo?.image_url ? <img src={mediaUrl(firstPromo.image_url)} alt={firstPromo.image_alt || firstPromo.title || "Offer"} loading="lazy" /> : null}
      </Link>

      <section className="content-section home-product-section home-product-section--dense">
        <div className="section-heading">
          <h2>In stock now</h2>
          <Link to="/catalog?in_stock=true">View all</Link>
        </div>
        <Alert>{inStockError}</Alert>
        <ProductGrid products={inStockProducts} loading={inStockLoading} skeletonCount={8} emptyTitle="No in-stock products found" />
      </section>

      <section className="content-section home-product-section">
        <div className="section-heading">
          <h2>Recommended now</h2>
          <Link to="/catalog">View all</Link>
        </div>
        <Alert>{recommendationsError}</Alert>
        <ProductGrid products={recommendations} loading={recommendationsLoading} skeletonCount={8} />
      </section>

      <section className="home-value-strip" aria-label="Store benefits">
        {valueProps.map((item) => (
          <div className="home-value-item" key={item.title}>
            <span>
              <MaterialIcon name={item.icon} size={20} />
            </span>
            <div>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </div>
          </div>
        ))}
      </section>

      <BrandStrip blocks={marketingByPlacement.brand_strip} />
    </div>
  );
}

function categoryUrl(category) {
  if (!category?.slug) return "/catalog";
  return `/catalog/category/${category.slug}`;
}

function ProductThumb({ product }) {
  const image = productImageUrl(product);

  return (
    <Link className="home-product-thumb" to={`/products/${product.id}`} title={product.title}>
      {image ? <img src={image} alt={product.title} loading="lazy" /> : <span>{productInitials(product.title)}</span>}
    </Link>
  );
}
