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
  const quantity = Math.max(1, Number(line.quantity || 1));
  const unitPrice =
    line.unit_price_incl_tax ??
    line.unit_price_excl_tax ??
    line.price_incl_tax ??
    line.price_excl_tax ??
    line.price ??
    product.price ??
    (Number(line.line_total || 0) / quantity || 0);
  const stockCount =
    product.stock ??
    product.stock_count ??
    product.num_in_stock ??
    product.availability?.num_available ??
    product.availability?.num_in_stock ??
    product.availability?.stock ??
    line.availability?.num_available;
  const hasStockCount = stockCount !== null && stockCount !== undefined && stockCount !== "";
  const isAvailable =
    product.is_available !== false &&
    product.availability?.is_available !== false &&
    line.availability?.is_available !== false &&
    (!hasStockCount || Number(stockCount) > 0);
  const stockText = isAvailable ? (hasStockCount ? `In stock ${stockCount}` : "In stock") : "Sold out";
  const productPath = product.id ? `/products/${product.id}` : "/catalog";

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
      <div className="cart-item__product">
        <Link className="cart-item__media" to={productPath}>
          {image ? <img src={image} alt={product.title || "Product"} /> : <span>{productInitials(product.title)}</span>}
        </Link>
        <div className="cart-item__body">
          <h3>
            <Link to={productPath}>{product.title || "Product"}</Link>
          </h3>
          <p className="cart-item__sku">
            <MaterialIcon name="tag" size={15} />
            {product.sku || line.line_reference || "Product line"}
          </p>
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
          <span className={`cart-item__stock ${isAvailable ? "is-in-stock" : "is-sold-out"}`}>
            <MaterialIcon name={isAvailable ? "check_circle" : "block"} size={15} />
            {stockText}
          </span>
        </div>
      </div>
      <div className="cart-item__unit-price" data-label="Price">
        <strong>{formatCurrency(unitPrice, line.currency)}</strong>
      </div>
      <div className="cart-item__quantity" data-label="Qty">
        <div className="qty-control">
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(Math.max(0, quantity - 1))} aria-label="Decrease quantity">
            <MaterialIcon name="remove" size={18} />
          </button>
          <span>{quantity}</span>
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(quantity + 1)} aria-label="Increase quantity">
            <MaterialIcon name="add" size={18} />
          </button>
        </div>
      </div>
      <div className="cart-item__line-total" data-label="Total">
        <strong>{formatCurrency(line.line_total, line.currency)}</strong>
        <button className="cart-save-button" type="button" disabled={loading} onClick={() => void handleSaveForLater()}>
          <MaterialIcon name="bookmark_add" size={18} />
          <span className="cart-save-button__label">Save for later</span>
        </button>
      </div>
      <button className="danger-link cart-item__remove" type="button" disabled={loading} onClick={() => void handleRemove()} aria-label="Remove item">
        <MaterialIcon name="delete" size={18} />
      </button>
    </article>
  );
}
