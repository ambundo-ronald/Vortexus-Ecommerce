import { useEffect, useState } from "react";
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

      <PromoBannerCarousel blocks={marketingByPlacement.promo_banner} />

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

      <BrandStrip blocks={marketingByPlacement.brand_strip} />
    </div>
  );
}

function PromoBannerCarousel({ blocks = [] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const slides = blocks.length
    ? blocks
    : [
        {
          id: "fallback-promo",
          eyebrow: "Flash sales",
          headline: "Ending in 2hrs",
          body: "Take a chance to buy within the time.",
          cta_text: "Shop the sale",
          cta_url: "/offers",
          image_url: "/hero%20landing%20images/television%20and%20sound%20system%20.png"
        }
      ];

  useEffect(() => {
    if (slides.length < 2) return undefined;

    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % slides.length);
    }, 4200);

    return () => window.clearInterval(timer);
  }, [slides.length]);

  useEffect(() => {
    setActiveIndex(0);
  }, [blocks.length]);

  return (
    <section className="home-deal-section" aria-label="Promotional banners">
      <div className="section-heading">
        <h2>Campaigns</h2>
        <Link to="/offers">View all</Link>
      </div>
      <div className="home-deal-carousel">
        <div className="home-deal-carousel__track" style={{ transform: `translateX(-${activeIndex * 100}%)` }}>
          {slides.map((slide, index) => (
            <PromoBannerSlide block={slide} key={slide.id || slide.slug || slide.image_url || slide.title} eager={index === 0} />
          ))}
        </div>
        {slides.length > 1 ? (
          <div className="home-deal-carousel__dots" aria-hidden="true">
            {slides.map((slide, index) => (
              <span className={index === activeIndex ? "active" : ""} key={slide.id || slide.slug || slide.image_url || slide.title} />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function PromoBannerSlide({ block, eager = false }) {
  const href = block.cta_url || "/offers";
  const external = /^https?:\/\//i.test(href);
  const imageUrl = block.id === "fallback-promo" ? block.image_url : mediaUrl(block.image_url);
  const content = (
    <>
      {imageUrl ? <img src={imageUrl} alt={block.image_alt || block.title || block.headline || "Promotion"} loading={eager ? "eager" : "lazy"} /> : null}
      <div>
        <span>{block.eyebrow || "Promo"}</span>
        <strong>{block.headline || block.title}</strong>
        {block.body ? <small>{block.body}</small> : null}
        <em>{block.cta_text || "Shop the sale"}</em>
      </div>
    </>
  );

  if (external) {
    return (
      <a className="home-deal-banner" href={href} target="_blank" rel="noreferrer">
        {content}
      </a>
    );
  }

  return (
    <Link className="home-deal-banner" to={href}>
      {content}
    </Link>
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
