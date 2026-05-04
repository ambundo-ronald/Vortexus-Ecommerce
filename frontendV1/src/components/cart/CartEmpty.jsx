import { Link } from "react-router-dom";

export default function CartEmpty() {
  return (
    <div className="empty-state">
      <strong>Your cart is empty</strong>
      <p>Add pumps, tanks, controllers, or treatment systems to start checkout.</p>
      <Link className="primary-button empty-state__action" to="/catalog">
        Browse catalog
      </Link>
    </div>
  );
}
