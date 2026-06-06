import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import WishlistButton from "../wishlist/WishlistButton.jsx";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";
import { productImageUrl } from "../../utils/productImages";
import { productInitials, productPrice, stockTone } from "../../utils/productDisplay";

export default function ProductCard({ product }) {
  const addItem = useCartStore((state) => state.addItem);
  const loading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const price = productPrice(product);
  const stock = stockTone(product);
  const reviewCount = Number(product.review_count ?? product.reviews_count ?? product.num_reviews ?? 0);
  const rating = Number(product.rating ?? product.average_rating ?? product.average_review_score ?? product.review_score ?? 0);
  const hasRating = Number.isFinite(rating) && rating > 0;
  const ratingText = hasRating ? rating.toFixed(1) : "New";
  const image = productImageUrl(product);
  const brandName = product.brand || product.brand_name || product.manufacturer || "";
  const brandSlug = product.brand_slug || slugify(brandName);
  const canAdd = stock.isAvailable && !price.isQuote;
  const discountBadge = price.discountLabel ? `${price.discountLabel.replace("-", "")} OFF` : "";

  async function handleAddToCart() {
    if (!stock.isAvailable) {
      notify({
        tone: "warning",
        title: "Sold out",
        message: `${product.title} is out of stock right now.`
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
      await addItem(product.id);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  return (
    <article className="product-card">
      <WishlistButton productId={product.id} productTitle={product.title} />
      <Link to={`/products/${product.id}`} className="product-card__media">
        {discountBadge ? <span className="product-card__sale-badge">{discountBadge}</span> : null}
        {image ? <img src={image} alt={product.title} loading="lazy" /> : <span className="product-card__placeholder">{productInitials(product.title)}</span>}
      </Link>
      <div className="product-card__body">
        <h3>
          <Link to={`/products/${product.id}`}>{product.title}</Link>
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
            className={`add-cart-button add-cart-button--icon${canAdd ? "" : " add-cart-button--muted"}`}
            type="button"
            disabled={loading}
            onClick={() => void handleAddToCart()}
            aria-label={canAdd ? `Add ${product.title} to cart` : `${product.title} is sold out`}
          >
            <MaterialIcon name="add_shopping_cart" size={18} />
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
