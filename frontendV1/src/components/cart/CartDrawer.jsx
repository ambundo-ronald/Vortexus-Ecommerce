import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCart } from "../../hooks/useCart";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";
import { productId, productInitials, productTitle } from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";
import "./CartDrawer.css";

export default function CartDrawer() {
  const open = useUiStore((state) => state.cartDrawerOpen);
  const close = useUiStore((state) => state.closeCartDrawer);
  const { basket, error } = useCart({ auto: open });
  const lines = basket.lines || [];
  const totals = basket.totals || {};
  const itemCount = basket.item_count || 0;

  return (
    <div className={`drawer-shell cart-drawer-shell ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="drawer-shade" type="button" onClick={close} aria-label="Close cart" />
      <aside className="drawer-panel cart-drawer" aria-label="Cart drawer">
        <div className="drawer-head cart-drawer__head">
          <div className="cart-drawer__title">
            <span>
              <MaterialIcon name="shopping_cart" size={22} />
            </span>
            <div>
              <strong>Cart</strong>
              <p>{itemCount} item{itemCount === 1 ? "" : "s"} ready</p>
            </div>
          </div>
          <button className="cart-drawer__close" type="button" onClick={close} aria-label="Close cart">
            <MaterialIcon name="close" size={22} />
          </button>
        </div>
        <Alert>{error}</Alert>
        <div className="drawer-scroll cart-drawer__scroll">
          {lines.length ? lines.map((line) => <DrawerCartItem key={line.id} line={line} onClick={close} />) : (
            <div className="empty-state cart-drawer__empty">
              <span>
                <MaterialIcon name="shopping_bag" size={30} />
              </span>
              <strong>Your cart is empty</strong>
              <p>Add products to see them here.</p>
              <Link className="primary-button" to="/catalog" onClick={close}>
                Browse products
              </Link>
            </div>
          )}
        </div>
        <div className="drawer-footer cart-drawer__footer">
          <div className="cart-drawer__totals">
            <span>Subtotal</span>
            <strong>{formatCurrency(totals.subtotal, totals.currency)}</strong>
          </div>
          <Link className="primary-button" to="/checkout/cart" onClick={close}>
            <MaterialIcon name="shopping_cart" size={19} />
            View cart
          </Link>
          <Link className="cart-drawer__continue" to="/catalog" onClick={close}>
            Continue shopping
          </Link>
        </div>
      </aside>
    </div>
  );
}

function DrawerCartItem({ line, onClick }) {
  const product = line.product || {};
  const title = productTitle({ ...line, product });
  const image = productImageUrl({ ...line, ...product, product });
  const resolvedProductId = productId({ ...line, product });

  return (
    <Link className="cart-drawer-item" to={resolvedProductId ? `/products/${resolvedProductId}` : "/catalog"} onClick={onClick}>
      <span className="cart-drawer-item__media">
        {image ? <img src={image} alt={title} /> : <em>{productInitials(title)}</em>}
      </span>
      <span className="cart-drawer-item__body">
        <strong>{title}</strong>
        <span>{formatCurrency(line.line_total, line.currency)}</span>
      </span>
    </Link>
  );
}
