import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCart } from "../../hooks/useCart";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";
import { productId, productInitials, productTitle } from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";
import "./CartDrawer.css";

const emptyCartImage = "/404 images/you cart is empty.png";

export default function CartDrawer() {
  const open = useUiStore((state) => state.cartDrawerOpen);
  const close = useUiStore((state) => state.closeCartDrawer);
  const { basket, error, loading, updateLine, removeLine, clearCart } = useCart({ auto: open });
  const lines = basket.lines || [];
  const totals = basket.totals || {};
  const itemCount = basket.item_count || 0;

  async function handleClearCart() {
    try {
      await clearCart?.();
    } catch {
      // The cart store already shows a notification for failed clearing.
    }
  }

  return (
    <div className={`drawer-shell cart-drawer-shell ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="drawer-shade" type="button" onClick={close} aria-label="Close cart" />
      <aside className="drawer-panel cart-drawer" aria-label="Cart drawer">
        <div className="drawer-head cart-drawer__head">
          <div className="cart-drawer__title">
            <span>
              <MaterialIcon name="shopping_cart" size={18} />
            </span>
            <div>
              <strong>Cart</strong>
            </div>
          </div>
          <button className="cart-drawer__close" type="button" onClick={close} aria-label="Close cart">
            <MaterialIcon name="close" size={21} />
          </button>
        </div>
        <Alert>{error}</Alert>
        <div className="drawer-scroll cart-drawer__scroll">
          {lines.length ? lines.map((line) => (
            <DrawerCartItem
              key={line.id}
              line={line}
              loading={loading}
              onClick={close}
              onRemove={removeLine}
              onUpdateQuantity={updateLine}
            />
          )) : (
            <div className="empty-state cart-drawer__empty">
              <img className="cart-drawer__empty-image" src={emptyCartImage} alt="Your cart is empty" />
              <strong>Your cart is empty</strong>
              <Link className="primary-button" to="/catalog" onClick={close}>
                Shop
              </Link>
            </div>
          )}
        </div>
        <div className="drawer-footer cart-drawer__footer">
          <div className="cart-drawer__totals">
            <span>Subtotal</span>
            <strong>{formatCurrency(totals.subtotal, totals.currency)}</strong>
          </div>
          <div className="cart-drawer__footer-actions">
            <Link className="primary-button cart-drawer__view-cart" to="/checkout/cart" onClick={close}>
              <MaterialIcon name="shopping_cart" size={18} />
              View cart
            </Link>
            {lines.length ? (
              <button className="cart-drawer__clear-text" type="button" disabled={loading} onClick={() => void handleClearCart()}>
                Clear cart
              </button>
            ) : null}
          </div>
          <Link className="cart-drawer__continue" to="/catalog" onClick={close}>
            Continue shopping
          </Link>
        </div>
      </aside>
    </div>
  );
}

function DrawerCartItem({ line, loading = false, onClick, onRemove, onUpdateQuantity }) {
  const product = line.product || {};
  const title = productTitle({ ...line, product });
  const image = productImageUrl({ ...line, ...product, product });
  const resolvedProductId = productId({ ...line, product });
  const quantity = Math.max(1, Number(line.quantity || 1));
  const productPath = resolvedProductId ? `/products/${resolvedProductId}` : "/catalog";

  async function handleQuantityChange(nextQuantity) {
    try {
      await onUpdateQuantity?.(line.id, nextQuantity);
    } catch {
      // The cart store already shows a notification for failed updates.
    }
  }

  async function handleRemove() {
    try {
      await onRemove?.(line.id);
    } catch {
      // The cart store already shows a notification for failed removal.
    }
  }

  return (
    <article className="cart-drawer-item">
      <Link className="cart-drawer-item__product" to={productPath} onClick={onClick}>
        <span className="cart-drawer-item__media">
          {image ? <img src={image} alt={title} /> : <em>{productInitials(title)}</em>}
        </span>
        <span className="cart-drawer-item__body">
          <strong>{title}</strong>
          <span>{formatCurrency(line.line_total, line.currency)}</span>
        </span>
      </Link>

      <div className="cart-drawer-item__controls" aria-label={`${title} quantity controls`}>
        <div className="cart-drawer-item__qty">
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(Math.max(0, quantity - 1))} aria-label="Decrease quantity">
            <MaterialIcon name="remove" size={16} />
          </button>
          <span>{quantity}</span>
          <button type="button" disabled={loading} onClick={() => void handleQuantityChange(quantity + 1)} aria-label="Increase quantity">
            <MaterialIcon name="add" size={16} />
          </button>
        </div>
        <button className="cart-drawer-item__delete" type="button" disabled={loading} onClick={() => void handleRemove()} aria-label="Remove item">
          <MaterialIcon name="delete" size={17} />
        </button>
      </div>
    </article>
  );
}
