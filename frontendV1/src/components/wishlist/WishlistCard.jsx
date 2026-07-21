import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { productId, productInitials, productPrice, productTitle, productUrl } from "../../utils/productDisplay";
import { productImageAlt, productImageUrl } from "../../utils/productImages";

export default function WishlistCard({ item, saving = false, onRemove }) {
  const product = item.product || item.wishlist_item?.product || {};
  const resolvedProductId = item.product_id || productId(product);
  const image = productImageUrl({ ...item, ...product, product });
  const title = productTitle({ ...item, product });
  const imageAlt = productImageAlt({ ...item, ...product, product }, title);
  const price = productPrice(product);
  const detailUrl = resolvedProductId ? productUrl({ ...item, product }) : "/catalog";

  return (
    <article className="wishlist-card">
      <Link className="wishlist-card__media" to={detailUrl}>
        {image ? (
          <img
            src={image}
            alt={imageAlt}
            loading="lazy"
            decoding="async"
            width="220"
            height="180"
          />
        ) : <span>{productInitials(title)}</span>}
      </Link>
      <div className="wishlist-card__body">
        <h3>
          <Link to={detailUrl}>{title}</Link>
        </h3>
        <strong>{price.label || "Quote on request"}</strong>
      </div>
      <button className="danger-link" type="button" disabled={saving || !resolvedProductId} onClick={() => onRemove?.(resolvedProductId)} aria-label="Remove from wishlist">
        <MaterialIcon name="delete" size={18} />
      </button>
    </article>
  );
}
