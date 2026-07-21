import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import HeroImageCarousel from "../../components/home/HeroImageCarousel.jsx";
import { AnnouncementStrip, BrandStrip, FeaturedMarketingBlocks, TopCategoryStrip } from "../../components/home/MarketingBlocks.jsx";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import Seo, { absoluteUrl } from "../../components/seo/Seo.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useMarketingBlocks } from "../../hooks/useMarketingBlocks";
import { useProducts } from "../../hooks/useProducts";
import { useRecommendations } from "../../hooks/useRecommendations";
import { useRecentlyBought } from "../../hooks/useRecentlyBought";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";
import { mediaUrl } from "../../utils/media";
import { productImageAlt, productImageUrl } from "../../utils/productImages";
import { productId, productInitials, productTitle, productUrl } from "../../utils/productDisplay";
import { groupMarketingBlocks } from "../../utils/marketingBlocks";
import "./HomePage.css";

export default function HomePage() {
  const { user, initialized: authInitialized } = useAuth();
  const hydrateCart = useCartStore((state) => state.hydrate);
  const notify = useUiStore((state) => state.notify);
  const {
    blocks: marketingBlocks,
    blocksByPlacement,
    loading: marketingLoading,
    error: marketingError
  } = useMarketingBlocks();
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
  const {
    products: recentlyBoughtProducts,
    loading: recentlyBoughtLoading,
    reordering: recentlyBoughtReordering,
    error: recentlyBoughtError,
    reorderRecentlyBought
  } = useRecentlyBought({ limit: 5 }, { auto: Boolean(user) });

  const marketingByPlacement = groupMarketingBlocks(marketingBlocks, blocksByPlacement);
  const newestPreview = newestProducts.length ? newestProducts.slice(0, 6) : recommendations.slice(0, 6);
  const showRecentlyBought =
    Boolean(user) && (recentlyBoughtLoading || recentlyBoughtProducts.length > 0 || recentlyBoughtError);

  async function handleReorderAll() {
    try {
      const payload = await reorderRecentlyBought({ limit: 5 });
      await hydrateCart();
      const addedCount = payload?.added?.length || 0;
      const skippedCount = payload?.skipped?.length || 0;
      notify({
        title: addedCount ? "Added to cart" : "Nothing added",
        message: skippedCount
          ? `${addedCount} product${addedCount === 1 ? "" : "s"} added. ${skippedCount} could not be added.`
          : `${addedCount} product${addedCount === 1 ? "" : "s"} added from your recent purchases.`,
        icon: "shopping_cart_checkout",
        tone: addedCount ? "success" : "warning"
      });
    } catch (error) {
      notify({
        tone: "danger",
        title: "Could not reorder",
        message: error?.normalized?.message || error.message || "Please try again.",
        icon: "error"
      });
    }
  }

  return (
    <div className="home-page">
      <Seo
        title="Reesolmart | Just in time, buying"
        description="Shop pumps, filters, tanks, water treatment systems, spares, and industrial supplies from Reesolmart."
        canonicalPath="/"
        jsonLd={[
          {
            "@context": "https://schema.org",
            "@type": "Organization",
            name: "Reesolmart",
            url: absoluteUrl("/"),
            logo: absoluteUrl("/Reesolmart logo.png"),
            email: "support@reesolmart.local",
            slogan: "Just in time, buying"
          },
          {
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: "Reesolmart",
            url: absoluteUrl("/"),
            potentialAction: {
              "@type": "SearchAction",
              target: `${absoluteUrl("/search")}?q={search_term_string}`,
              "query-input": "required name=search_term_string"
            }
          }
        ]}
      />
      <AnnouncementStrip blocks={marketingByPlacement.announcement} />

      <section className="home-showcase" aria-label="Store highlights">
        <div className="home-showcase__main">
          <HeroImageCarousel
            blocks={marketingByPlacement.home_hero}
            loading={marketingLoading}
          />
          <section className="home-arrivals-strip" aria-label="New arrivals preview">
            <div>
              <strong>New arrivals</strong>
              <Link to="/catalog?sort_by=newest">
                View all
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

      <TopCategoryStrip blocks={marketingByPlacement.top_category} />

      <FeaturedMarketingBlocks blocks={marketingByPlacement.featured} />

      {showRecentlyBought ? (
        <section className="content-section home-product-section">
          <div className="section-heading">
            <h2>Recently bought</h2>
            <button
              className="section-heading__button"
              type="button"
              disabled={recentlyBoughtReordering || !recentlyBoughtProducts.length}
              onClick={() => void handleReorderAll()}
            >
              <MaterialIcon name={recentlyBoughtReordering ? "progress_activity" : "shopping_cart_checkout"} size={17} />
              <span>{recentlyBoughtReordering ? "Adding..." : "Reorder all"}</span>
            </button>
          </div>
          <Alert>{recentlyBoughtError}</Alert>
          <ProductGrid
            products={recentlyBoughtProducts}
            loading={recentlyBoughtLoading && authInitialized}
            skeletonCount={5}
            cardActionVariant="reorder"
          />
        </section>
      ) : null}

      <section className="content-section home-product-section">
        <div className="section-heading">
          <h2>New arrivals</h2>
          <Link to="/catalog?sort_by=newest">View all</Link>
        </div>
        <Alert>{newestError || recommendationsError}</Alert>
        <ProductGrid products={newestProducts.slice(0, 5).length ? newestProducts.slice(0, 5) : recommendations.slice(0, 5)} loading={newestLoading || recommendationsLoading} skeletonCount={5} />
      </section>

      <PromoBannerCarousel blocks={marketingByPlacement.promo_banner} loading={marketingLoading} />

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
          <h2>Recommended</h2>
          <Link to="/catalog">View all</Link>
        </div>
        <Alert>{recommendationsError}</Alert>
        <ProductGrid products={recommendations} loading={recommendationsLoading} skeletonCount={8} />
      </section>
    </div>
  );
}

function PromoBannerCarousel({ blocks = [], loading = false }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const slides = blocks;

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

  if (loading && !slides.length) {
    return <section className="home-deal-carousel skeleton-block" aria-label="Loading promotional banners" />;
  }

  if (!slides.length) return null;

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
  const imageUrl = mediaUrl(block.image_url);
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
  const imageAlt = productImageAlt(product, title);

  return (
    <Link className="home-product-thumb" to={id ? productUrl(product) : "/catalog"} title={title}>
      {image ? (
        <img
          src={image}
          alt={imageAlt}
          loading="lazy"
          decoding="async"
          width="220"
          height="160"
        />
      ) : <span>{productInitials(title)}</span>}
    </Link>
  );
}
