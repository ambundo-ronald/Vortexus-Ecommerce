import { useEffect, useMemo, useState } from "react";

import { productImageList } from "../../utils/productImages";
import { productInitials } from "../../utils/productDisplay";

const MOBILE_CAROUSEL_DELAY = 3200;

export default function ProductImageGallery({ product }) {
  const images = useMemo(() => {
    return productImageList(product);
  }, [product]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [zoomOrigin, setZoomOrigin] = useState("50% 50%");
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    setActiveIndex(0);
  }, [product?.id]);

  useEffect(() => {
    if (images.length <= 1) return undefined;
    if (isPaused) return undefined;
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return undefined;
    const mediaQuery = window.matchMedia("(max-width: 759px)");
    if (!mediaQuery.matches) return undefined;

    const intervalId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % images.length);
    }, MOBILE_CAROUSEL_DELAY);

    return () => window.clearInterval(intervalId);
  }, [images.length, isPaused]);

  function moveZoom(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    setZoomOrigin(`${Math.max(0, Math.min(100, x))}% ${Math.max(0, Math.min(100, y))}%`);
  }

  return (
    <div className="product-gallery-shell">
      <div
        className="product-gallery"
        onFocus={() => setIsPaused(true)}
        onBlur={() => setIsPaused(false)}
        onMouseEnter={() => setIsPaused(true)}
        onMouseMove={moveZoom}
        onMouseLeave={() => {
          setZoomOrigin("50% 50%");
          setIsPaused(false);
        }}
      >
        {images.length ? (
          <div className="product-gallery-track" style={{ transform: `translateX(-${activeIndex * 100}%)` }}>
            {images.map((image, index) => (
              <div className={`product-gallery-slide${index === activeIndex ? " is-active" : ""}`} key={`${image}-${index}`}>
                <img
                  src={image}
                  alt={index === activeIndex ? product?.title || "Product" : ""}
                  style={index === activeIndex ? { transformOrigin: zoomOrigin } : undefined}
                />
              </div>
            ))}
          </div>
        ) : (
          <span className="product-gallery__placeholder">{productInitials(product?.title)}</span>
        )}
      </div>
      <div className="product-gallery-thumbs" aria-label="Product images">
        {Array.from({ length: Math.max(1, Math.min(4, images.length || 1)) }).map((_, index) => {
          const image = images[index];
          return (
            <button
              className={index === activeIndex ? "active" : ""}
              type="button"
              key={image || index}
              onClick={() => setActiveIndex(index)}
              disabled={!image}
              aria-label={`View product image ${index + 1}`}
            >
              {image ? <img src={image} alt="" /> : <span>{productInitials(product?.title)}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
