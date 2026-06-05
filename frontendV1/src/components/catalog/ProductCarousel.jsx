import { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import WishlistButton from "../wishlist/WishlistButton.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";
import { useWishlistStore } from "../../store/wishlist.store";
import { productImageUrl } from "../../utils/productImages";
import { productId, productPrice, productTitle, stockTone } from "../../utils/productDisplay";

const fallbackSlides = [
  { title: "Borehole pumps", tone: "blue" },
  { title: "Pressure tanks", tone: "slate" },
  { title: "Water treatment", tone: "green" },
  { title: "Controllers", tone: "gold" }
];

export default function ProductCarousel({ products = [], loading = false }) {
  const scrollRef = useRef(null);
  const addItem = useCartStore((state) => state.addItem);
  const cartLoading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);

  const slides = useMemo(() => {
    if (products.length) return products.slice(0, 10);
    return fallbackSlides;
  }, [products]);

  const slideIds = useMemo(() => slides.map((product) => productId(product)).filter(Boolean), [slides]);

  useEffect(() => {
    if (user && slideIds.length) void loadStatus(slideIds);
  }, [loadStatus, slideIds, user]);

  function scrollBy(direction) {
    const node = scrollRef.current;
    if (!node) return;
    node.scrollBy({ left: direction * Math.min(node.clientWidth, 520), behavior: "smooth" });
  }

  async function handleAddToCart(product) {
    const stock = stockTone(product);
    const price = productPrice(product);
    if (!stock.isAvailable) {
      notify({
        tone: "warning",
        title: "Sold out",
        message: `${productTitle(product)} is out of stock right now.`
      });
      return;
    }
    if (price.isQuote) {
      notify({
        tone: "warning",
        title: "Price unavailable",
        message: "Request a quote for this product before checkout."
      });
      return;
    }
    try {
      await addItem(productId(product));
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  if (loading) {
    return (
      <section className="commerce-carousel commerce-carousel--loading" aria-label="Loading featured products">
        <div className="carousel-track">
          {Array.from({ length: 4 }).map((_, index) => (
            <div className="promo-slide skeleton-block" key={index} />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="commerce-carousel" aria-label="Featured products">
      <button className="carousel-button carousel-button--left" type="button" onClick={() => scrollBy(-1)} aria-label="Previous products">
        <MaterialIcon name="chevron_left" size={22} />
      </button>
      <div className="carousel-track" ref={scrollRef}>
        {slides.map((product, index) => {
          const resolvedProductId = productId(product);
          const title = productTitle(product);
          const hasProduct = Boolean(resolvedProductId);
          const image = hasProduct ? productImageUrl(product) : "";
          const price = hasProduct ? productPrice(product) : null;
          const stock = hasProduct ? stockTone(product) : null;
          const canAdd = hasProduct && stock.isAvailable && !price.isQuote;

          return (
            <article className={`promo-slide promo-slide--${product.tone || "blue"}`} key={resolvedProductId || title}>
              {hasProduct ? <WishlistButton productId={resolvedProductId} productTitle={title} /> : null}
              <Link className="promo-slide__media" to={hasProduct ? `/products/${resolvedProductId}` : "/catalog"}>
                {image ? <img src={image} alt={title} loading={index === 0 ? "eager" : "lazy"} /> : <span>{title}</span>}
              </Link>
              <div className="promo-slide__content">
                <Link to={hasProduct ? `/products/${resolvedProductId}` : "/catalog"}>
                  <strong>{title}</strong>
                </Link>
                {hasProduct ? (
                  <>
                    <span className={`stock-label stock-label--${stock.isAvailable ? "available" : "sold-out"}`}>{stock.label}</span>
                    <div className="promo-slide__meta">
                      <span>{price.label}</span>
                      <button
                        className={`icon-action${canAdd ? "" : " icon-action--muted"}`}
                        type="button"
                        disabled={cartLoading}
                        onClick={() => void handleAddToCart(product)}
                        aria-label={canAdd ? `Add ${title} to cart` : `${title} is sold out`}
                      >
                        <MaterialIcon name="add_shopping_cart" size={18} />
                      </button>
                    </div>
                  </>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
      <button className="carousel-button carousel-button--right" type="button" onClick={() => scrollBy(1)} aria-label="Next products">
        <MaterialIcon name="chevron_right" size={22} />
      </button>
    </section>
  );
}
