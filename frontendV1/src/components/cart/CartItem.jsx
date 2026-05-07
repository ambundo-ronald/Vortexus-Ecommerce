import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCartStore } from "../../store/cart.store";
import { formatCurrency } from "../../utils/currency";
import { productPlaceholderImage } from "../../utils/productImages";

export default function CartItem({ line }) {
  const updateLine = useCartStore((state) => state.updateLine);
  const removeLine = useCartStore((state) => state.removeLine);
  const loading = useCartStore((state) => state.loading);
  const product = line.product || {};

  return (
    <article className="cart-item">
      <Link className="cart-item__media" to={`/products/${product.id}`}>
        <img src={productPlaceholderImage()} alt={product.title || "Product"} />
      </Link>
      <div className="cart-item__body">
        <h3>
          <Link to={`/products/${product.id}`}>{product.title}</Link>
        </h3>
        <p>{product.sku || line.line_reference}</p>
        <strong>{formatCurrency(line.line_total, line.currency)}</strong>
      </div>
      <div className="cart-item__actions">
        <div className="qty-control">
          <button type="button" disabled={loading} onClick={() => void updateLine(line.id, Math.max(0, line.quantity - 1))} aria-label="Decrease quantity">
            <MaterialIcon name="remove" size={18} />
          </button>
          <span>{line.quantity}</span>
          <button type="button" disabled={loading} onClick={() => void updateLine(line.id, line.quantity + 1)} aria-label="Increase quantity">
            <MaterialIcon name="add" size={18} />
          </button>
        </div>
        <button className="danger-link" type="button" disabled={loading} onClick={() => void removeLine(line.id)} aria-label="Remove item">
          <MaterialIcon name="delete" size={18} />
        </button>
      </div>
    </article>
  );
}
