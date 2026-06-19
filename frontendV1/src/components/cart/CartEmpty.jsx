import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const emptyCartImage = "/404 images/you cart is empty.png";

export default function CartEmpty() {
  return (
    <div className="cart-empty-state">
      <img className="cart-empty-state__image" src={emptyCartImage} alt="Your cart is empty" />
      <div>
        <strong>Your cart is empty</strong>
      </div>
      <div className="cart-empty-state__actions">
        <Link className="primary-button empty-state__action" to="/offers">
          <MaterialIcon name="local_offer" size={18} />
          View offers
        </Link>
        <Link className="secondary-button" to="/catalog">
          <MaterialIcon name="shopping_bag" size={18} />
          Shop products
        </Link>
      </div>
    </div>
  );
}
