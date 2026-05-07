import { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import WishlistButton from "../wishlist/WishlistButton.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cart.store";
import { useWishlistStore } from "../../store/wishlist.store";
import { productPlaceholderImage } from "../../utils/productImages";
import { productPrice } from "../../utils/productDisplay";

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
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);

  const slides = useMemo(() => {
    if (products.length) return products.slice(0, 10);
    return fallbackSlides;
  }, [products]);

  const slideIds = useMemo(() => slides.map((product) => product.id).filter(Boolean), [slides]);

  useEffect(() => {
    if (user && slideIds.length) void loadStatus(slideIds);
  }, [loadStatus, slideIds, user]);

  function scrollBy(direction) {
    const node = scrollRef.current;
    if (!node) return;
    node.scrollBy({ left: direction * Math.min(node.clientWidth, 520), behavior: "smooth" });
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
          const hasProduct = Boolean(product.id);
          const image = hasProduct ? productPlaceholderImage(index % 4) : "";
          const price = hasProduct ? productPrice(product) : null;
          const canAdd = hasProduct && product.in_stock && !price.isQuote;

          return (
            <article className={`promo-slide promo-slide--${product.tone || "blue"}`} key={product.id || product.title}>
              {hasProduct ? <WishlistButton productId={product.id} productTitle={product.title} /> : null}
              <Link className="promo-slide__media" to={hasProduct ? `/products/${product.id}` : "/catalog"}>
                {image ? <img src={image} alt={product.title} loading={index === 0 ? "eager" : "lazy"} /> : <span>{product.title}</span>}
              </Link>
              <div className="promo-slide__content">
                <Link to={hasProduct ? `/products/${product.id}` : "/catalog"}>
                  <strong>{product.title}</strong>
                </Link>
                {hasProduct ? (
                  <div className="promo-slide__meta">
                    <span>{price.label}</span>
                    {canAdd ? (
                      <button
                        className="icon-action"
                        type="button"
                        disabled={cartLoading}
                        onClick={() => void addItem(product.id)}
                        aria-label={`Add ${product.title} to cart`}
                      >
                        <MaterialIcon name="add_shopping_cart" size={18} />
                      </button>
                    ) : (
                      <Link className="icon-action" to={`/products/${product.id}`} aria-label={`View ${product.title}`}>
                        <MaterialIcon name="visibility" size={18} />
                      </Link>
                    )}
                  </div>
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
