import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCartStore } from "../../store/cart.store";
import { formatCurrency } from "../../utils/currency";
import { productInitials } from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";

export default function CartItem({ line }) {
  const updateLine = useCartStore((state) => state.updateLine);
  const removeLine = useCartStore((state) => state.removeLine);
  const saveLineForLater = useCartStore((state) => state.saveLineForLater);
  const loading = useCartStore((state) => state.loading);
  const product = line.product || {};
  const image = productImageUrl(product);
  const options = line.options || [];

  async function handleQuantityChange(quantity) {
    try {
      await updateLine(line.id, quantity);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  async function handleRemove() {
    try {
      await removeLine(line.id);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  async function handleSaveForLater() {
    try {
      await saveLineForLater(line.id);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  return (
    <article className="cart-item">
      <Link className="cart-item__media" to={`/products/${product.id}`}>
        {image ? <img src={image} alt={product.title || "Product"} /> : <span>{productInitials(product.title)}</span>}
      </Link>
      <div className="cart-item__body">
        <h3>
          <Link to={`/products/${product.id}`}>{product.title}</Link>
        </h3>
        <p>{product.sku || line.line_reference}</p>
        {options.length ? (
          <ul className="cart-item__options">
            {options.map((option) => (
              <li key={option.id || option.code}>
                <span>{option.name || option.code}</span>
                <strong>{option.value}</strong>
              </li>
            ))}
          </ul>
        ) : null}
        <strong>{formatCurrency(line.line_total, line.currency)}</strong>
      </div>
      <div className="cart-item__actions">
        <div className="qty-control">
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(Math.max(0, line.quantity - 1))} aria-label="Decrease quantity">
            <MaterialIcon name="remove" size={18} />
          </button>
          <span>{line.quantity}</span>
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(line.quantity + 1)} aria-label="Increase quantity">
            <MaterialIcon name="add" size={18} />
          </button>
        </div>
        <button className="danger-link" type="button" disabled={loading} onClick={() => void handleRemove()} aria-label="Remove item">
          <MaterialIcon name="delete" size={18} />
        </button>
        <button className="cart-save-button" type="button" disabled={loading} onClick={() => void handleSaveForLater()}>
          <MaterialIcon name="bookmark_add" size={18} />
          Save
        </button>
      </div>
    </article>
  );
}
