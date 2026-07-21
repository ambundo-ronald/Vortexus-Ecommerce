import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import WishlistButton from "../wishlist/WishlistButton.jsx";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";
import { productImageAlt, productImageUrl } from "../../utils/productImages";
import { productBrand, productId, productInitials, productPrice, productRating, productTitle, productUrl, stockTone } from "../../utils/productDisplay";
import { rememberSearchContext, searchAttributionMetadata, trackStorefrontEvent } from "../../utils/analytics";

export default function ProductCard({ product, actionVariant = "add", analyticsContext = null }) {
  const addItem = useCartStore((state) => state.addItem);
  const loading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const price = productPrice(product);
  const stock = stockTone(product);
  const resolvedProductId = productId(product);
  const title = productTitle(product);
  const { rating, reviewCount, hasRating } = productRating(product);
  const ratingText = hasRating ? rating.toFixed(1) : "New";
  const image = productImageUrl(product);
  const imageAlt = productImageAlt(product, title);
  const brandName = productBrand(product);
  const brandSlug = product.brand_slug || slugify(brandName);
  const detailUrl = productUrl(product);
  const canAdd = stock.isAvailable && !price.isQuote;
  const discountBadge = price.discountLabel ? `${price.discountLabel.replace("-", "")} OFF` : "";
  const isReorder = actionVariant === "reorder";
  const reorderQuantity = Math.max(Number(product?.recent_order_quantity) || 1, 1);

  async function handleAddToCart() {
    if (!stock.isAvailable) {
      notify({
        tone: "warning",
        title: "Sold out",
        message: `${title} is out of stock right now.`
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
      await addItem(resolvedProductId, isReorder ? reorderQuantity : 1, [], searchAttributionMetadata({
        product_id: Number(resolvedProductId),
        product_title: title
      }));
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  function trackProductClick() {
    if (!resolvedProductId) return;
    const context = analyticsContext ? rememberSearchContext(analyticsContext) : null;
    trackStorefrontEvent("product_clicked", {
      ...(context || searchAttributionMetadata()),
      product_id: Number(resolvedProductId),
      product_title: title,
      source: context?.source || "search"
    });
  }

  return (
    <article className={`product-card${isReorder ? " product-card--reorder" : ""}`}>
      <WishlistButton productId={resolvedProductId} productTitle={title} />
      <Link to={resolvedProductId ? detailUrl : "/catalog"} className="product-card__media" onClick={trackProductClick}>
        {discountBadge ? <span className="product-card__sale-badge">{discountBadge}</span> : null}
        {image ? (
          <img
            src={image}
            alt={imageAlt}
            loading="lazy"
            decoding="async"
            width="420"
            height="320"
          />
        ) : <span className="product-card__placeholder">{productInitials(title)}</span>}
      </Link>
      <div className="product-card__body">
        <h3>
          <Link to={resolvedProductId ? detailUrl : "/catalog"} onClick={trackProductClick}>{title}</Link>
        </h3>
        {brandName ? <Link className="product-card__brand" to={`/catalog/brand/${encodeURIComponent(brandSlug)}`}>{brandName}</Link> : null}
        <span className="product-card__price">
          <span className={price.previousLabel ? "product-card__price-row product-card__price-row--discounted" : "product-card__price-row"}>
            <strong>{price.label}</strong>
            {price.previousLabel ? <small className="product-card__previous-price">{price.previousLabel}</small> : null}
          </span>
          {price.sublabel ? <small>{price.sublabel}</small> : null}
        </span>
        <div className={`product-card__rating${hasRating ? "" : " is-empty"}`} aria-label={reviewCount > 0 ? `${ratingText} out of 5 from ${reviewCount} reviews` : "No reviews yet"}>
          <MaterialIcon name="star" size={15} filled={hasRating} className="product-card__rating-icon" />
          <span className="product-card__rating-value">{ratingText}</span>
          {reviewCount > 0 ? <span className="product-card__rating-count">({reviewCount})</span> : null}
        </div>
        <span className={`stock-label stock-label--${stock.isAvailable ? "available" : "sold-out"}`}>{stock.label}</span>
        <div className="product-card__foot">
          <button
            className={`add-cart-button ${isReorder ? "add-cart-button--reorder" : "add-cart-button--icon"}${canAdd ? "" : " add-cart-button--muted"}`}
            type="button"
            disabled={loading || !resolvedProductId}
            onClick={() => void handleAddToCart()}
            aria-label={canAdd ? `${isReorder ? "Reorder" : "Add"} ${title}` : `${title} is sold out`}
          >
            <MaterialIcon name={isReorder ? "refresh" : "add_shopping_cart"} size={18} />
            {isReorder ? <span>Reorder</span> : null}
          </button>
        </div>
      </div>
    </article>
  );
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
