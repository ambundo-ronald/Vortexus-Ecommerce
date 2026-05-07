import { Link } from "react-router-dom";

import CartItem from "./CartItem.jsx";
import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCart } from "../../hooks/useCart";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";

export default function CartDrawer() {
  const open = useUiStore((state) => state.cartDrawerOpen);
  const close = useUiStore((state) => state.closeCartDrawer);
  const { basket, error } = useCart({ auto: open });
  const lines = basket.lines || [];
  const totals = basket.totals || {};

  return (
    <div className={`drawer-shell ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="drawer-shade" type="button" onClick={close} aria-label="Close cart" />
      <aside className="drawer-panel" aria-label="Cart drawer">
        <div className="drawer-head">
          <strong>Cart</strong>
          <button type="button" onClick={close} aria-label="Close cart">
            <MaterialIcon name="close" size={22} />
          </button>
        </div>
        <Alert>{error}</Alert>
        <div className="drawer-scroll">
          {lines.length ? lines.map((line) => <CartItem key={line.id} line={line} />) : (
            <div className="empty-state">
              <strong>Your cart is empty</strong>
              <p>Add products to see them here.</p>
            </div>
          )}
        </div>
        <div className="drawer-footer">
          <div className="summary-row">
            <span>Subtotal</span>
            <strong>{formatCurrency(totals.subtotal, totals.currency)}</strong>
          </div>
          <Link className="primary-button" to="/checkout/cart" onClick={close}>
            <MaterialIcon name="shopping_cart" size={19} />
            View cart
          </Link>
        </div>
      </aside>
    </div>
  );
}
