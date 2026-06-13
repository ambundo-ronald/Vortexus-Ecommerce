import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { productImageUrl } from "../../utils/productImages";

export default function SupplierProductTable({ products = [], loading = false, onEdit, onDelete, deletingId = null }) {
  if (loading) {
    return (
      <div className="supplier-empty-state">
        <MaterialIcon name="hourglass_top" size={24} />
        <strong>Loading products</strong>
      </div>
    );
  }

  if (!products.length) {
    return (
      <div className="supplier-empty-state">
        <MaterialIcon name="inventory_2" size={28} />
        <strong>No supplier products yet</strong>
        <span>Add your first product and submit it for review.</span>
      </div>
    );
  }

  return (
    <div className="supplier-table">
      <div className="supplier-table__head supplier-table__row">
        <span>Product</span>
        <span>Offer</span>
        <span>Status</span>
        <span>Actions</span>
      </div>
      {products.map((product) => (
        <div className="supplier-table__row" key={product.id}>
          <div className="supplier-product-cell">
            <div className="supplier-product-cell__image">
              {productImageUrl(product) ? <img src={productImageUrl(product)} alt="" /> : <MaterialIcon name="inventory_2" size={22} />}
            </div>
            <div>
              <strong>{product.title}</strong>
              <span>{product.upc || product.sku || "No SKU"}</span>
            </div>
          </div>
          <div>
            <strong>{money(product.offer?.price, product.offer?.currency || product.currency)}</strong>
            <span>{Number(product.offer?.num_in_stock || 0).toLocaleString()} in stock</span>
          </div>
          <div>
            <ModerationBadge status={product.moderation?.status} />
            {product.moderation?.review_note ? <span className="supplier-review-note">{product.moderation.review_note}</span> : null}
          </div>
          <div className="supplier-table__actions">
            {product.is_public ? (
              <Link className="icon-action-button" to={`/products/${product.id}`} aria-label="View product">
                <MaterialIcon name="open_in_new" size={18} />
              </Link>
            ) : null}
            <button className="secondary-button" type="button" onClick={() => onEdit?.(product)}>
              <MaterialIcon name="edit" size={18} />
              Edit
            </button>
            <button
              className="danger-link supplier-product-delete"
              type="button"
              disabled={deletingId === product.id}
              onClick={() => onDelete?.(product)}
              aria-label={`Remove ${product.title}`}
            >
              <MaterialIcon name={deletingId === product.id ? "hourglass_top" : "delete"} size={18} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function ModerationBadge({ status }) {
  const normalized = status || "pending_review";
  return <span className={`supplier-status supplier-status--${normalized}`}>{formatStatus(normalized)}</span>;
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function money(value, currency = "KES") {
  if (value === null || value === undefined || value === "") return "No price";
  return `${currency || "KES"} ${Number(value).toLocaleString()}`;
}
