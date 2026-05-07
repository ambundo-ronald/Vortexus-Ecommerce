import { useEffect, useMemo, useState } from "react";

import { productImageList } from "../../utils/productImages";
import { productInitials } from "../../utils/productDisplay";

export default function ProductImageGallery({ product }) {
  const images = useMemo(() => {
    return productImageList(product);
  }, [product]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [zoomOrigin, setZoomOrigin] = useState("50% 50%");
  const activeImage = images[activeIndex];

  useEffect(() => {
    setActiveIndex(0);
  }, [product?.id]);

  function moveZoom(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    setZoomOrigin(`${Math.max(0, Math.min(100, x))}% ${Math.max(0, Math.min(100, y))}%`);
  }

  return (
    <div className="product-gallery-shell">
      <div className="product-gallery" onMouseMove={moveZoom} onMouseLeave={() => setZoomOrigin("50% 50%")}>
        {activeImage ? (
          <img src={activeImage} alt={product?.title || "Product"} style={{ transformOrigin: zoomOrigin }} />
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
