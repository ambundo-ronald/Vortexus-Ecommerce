import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import HeroImageCarousel from "../../components/home/HeroImageCarousel.jsx";
import { AnnouncementStrip, BrandStrip, FeaturedMarketingBlocks } from "../../components/home/MarketingBlocks.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useMarketingBlocks } from "../../hooks/useMarketingBlocks";
import { useProducts } from "../../hooks/useProducts";
import { useRecommendations } from "../../hooks/useRecommendations";
import { mediaUrl } from "../../utils/media";
import { productImageUrl } from "../../utils/productImages";
import { productId, productInitials, productTitle } from "../../utils/productDisplay";
import "./HomePage.css";

export default function HomePage() {
  const { blocks: marketingBlocks, loading: marketingLoading } = useMarketingBlocks();
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
  const newestPreview = newestProducts.length ? newestProducts.slice(0, 6) : recommendations.slice(0, 6);

  return (
    <div className="home-page">
      <AnnouncementStrip blocks={marketingByPlacement.announcement} />

      <section className="home-showcase" aria-label="Store highlights">
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
                : newestPreview.map((product) => <ProductThumb key={productId(product) || productTitle(product)} product={product} />)}
            </div>
          </section>
        </div>
      </section>

      <BrandStrip blocks={marketingByPlacement.brand_strip} />

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

function ProductThumb({ product }) {
  const id = productId(product);
  const title = productTitle(product);
  const image = productImageUrl(product);

  return (
    <Link className="home-product-thumb" to={id ? `/products/${id}` : "/catalog"} title={title}>
      {image ? <img src={image} alt={title} loading="lazy" /> : <span>{productInitials(title)}</span>}
    </Link>
  );
}
