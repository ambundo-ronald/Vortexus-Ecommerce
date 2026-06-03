import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function CartEmpty() {
  return (
    <div className="empty-state cart-empty-state">
      <span className="cart-empty-state__icon">
        <MaterialIcon name="shopping_cart" size={30} />
      </span>
      <div>
        <strong>Your cart is empty</strong>
        <p>Add pumps, tanks, controllers, or treatment systems to start checkout.</p>
      </div>
      <div className="cart-empty-state__actions">
        <Link className="primary-button empty-state__action" to="/catalog">
          <MaterialIcon name="shopping_bag" size={18} />
          Shop products
        </Link>
        <Link className="secondary-button" to="/offers">
          <MaterialIcon name="local_offer" size={18} />
          View offers
        </Link>
      </div>
    </div>
  );
}
