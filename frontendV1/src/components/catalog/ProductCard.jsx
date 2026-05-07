import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import StarRating from "../reviews/StarRating.jsx";
import WishlistButton from "../wishlist/WishlistButton.jsx";
import { useCartStore } from "../../store/cart.store";
import { productPlaceholderImage } from "../../utils/productImages";
import { productPrice } from "../../utils/productDisplay";

export default function ProductCard({ product }) {
  const addItem = useCartStore((state) => state.addItem);
  const loading = useCartStore((state) => state.loading);
  const price = productPrice(product);
  const reviewCount = Number(product.review_count || 0);
  const rating = Number(product.rating || 0);

  return (
    <article className="product-card">
      <WishlistButton productId={product.id} productTitle={product.title} />
      <Link to={`/products/${product.id}`} className="product-card__media">
        <img src={productPlaceholderImage()} alt={product.title} loading="lazy" />
      </Link>
      <div className="product-card__body">
        <h3>
          <Link to={`/products/${product.id}`}>{product.title}</Link>
        </h3>
        {reviewCount > 0 ? (
          <div className="product-card__rating" aria-label={`${rating} out of 5 from ${reviewCount} reviews`}>
            <StarRating value={rating} size={14} />
            <span>{reviewCount}</span>
          </div>
        ) : null}
        <div className="product-card__foot">
          <span className="product-card__price">
            <strong>{price.label}</strong>
            {price.sublabel ? <small>{price.sublabel}</small> : null}
          </span>
          <button
            className="add-cart-button add-cart-button--icon"
            type="button"
            disabled={loading}
            onClick={() => void addItem(product.id)}
            aria-label={`Add ${product.title} to cart`}
          >
            <MaterialIcon name="add_shopping_cart" size={18} />
          </button>
        </div>
      </div>
    </article>
  );
}
