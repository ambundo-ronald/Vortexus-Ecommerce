import { useMemo, useState } from "react";

import { PRODUCT_PLACEHOLDER_IMAGES } from "../../utils/productImages";
import { productInitials } from "../../utils/productDisplay";

export default function ProductImageGallery({ product }) {
  const images = useMemo(() => {
    return PRODUCT_PLACEHOLDER_IMAGES;
  }, []);
  const [activeIndex, setActiveIndex] = useState(0);
  const [zoomOrigin, setZoomOrigin] = useState("50% 50%");
  const activeImage = images[activeIndex];

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
        {Array.from({ length: 4 }).map((_, index) => {
          const image = images[index];
          return (
            <button
              className={index === activeIndex ? "active" : ""}
              type="button"
              key={image || index}
              onClick={() => setActiveIndex(index)}
              disabled={!image}
              aria-label={`View angle ${index + 1}`}
            >
              {image ? <img src={image} alt="" /> : <span>{index + 1}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
