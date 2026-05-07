import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";
import { productPlaceholderImage } from "../../utils/productImages";

export default function WishlistCard({ item, index = 0, saving = false, onRemove }) {
  const product = item.product || {};
  const productId = item.product_id || product.id;

  return (
    <article className="wishlist-card">
      <Link className="wishlist-card__media" to={productId ? `/products/${productId}` : "/catalog"}>
        <img src={productPlaceholderImage(index)} alt={item.title || product.title || "Product"} />
      </Link>
      <div className="wishlist-card__body">
        <h3>
          <Link to={productId ? `/products/${productId}` : "/catalog"}>{item.title || product.title || "Product"}</Link>
        </h3>
        <strong>{formatCurrency(product.base_price ?? product.price, product.base_currency || product.currency)}</strong>
      </div>
      <button className="danger-link" type="button" disabled={saving || !productId} onClick={() => onRemove?.(productId)} aria-label="Remove from wishlist">
        <MaterialIcon name="delete" size={18} />
      </button>
    </article>
  );
}
