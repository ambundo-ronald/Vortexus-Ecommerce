import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";
import { productInitials } from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";

export default function WishlistCard({ item, saving = false, onRemove }) {
  const product = item.product || {};
  const productId = item.product_id || product.id;
  const image = productImageUrl({ ...product, thumbnail: item.thumbnail || product.thumbnail });
  const title = item.title || product.title || "Product";

  return (
    <article className="wishlist-card">
      <Link className="wishlist-card__media" to={productId ? `/products/${productId}` : "/catalog"}>
        {image ? <img src={image} alt={title} /> : <span>{productInitials(title)}</span>}
      </Link>
      <div className="wishlist-card__body">
        <h3>
          <Link to={productId ? `/products/${productId}` : "/catalog"}>{title}</Link>
        </h3>
        <strong>{formatCurrency(product.base_price ?? product.price, product.base_currency || product.currency)}</strong>
      </div>
      <button className="danger-link" type="button" disabled={saving || !productId} onClick={() => onRemove?.(productId)} aria-label="Remove from wishlist">
        <MaterialIcon name="delete" size={18} />
      </button>
    </article>
  );
}
