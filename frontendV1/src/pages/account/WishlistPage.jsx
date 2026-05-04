import { Link } from "react-router-dom";

import WishlistCard from "../../components/wishlist/WishlistCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useWishlist } from "../../hooks/useWishlist";

export default function WishlistPage() {
  const { wishlist, items, loading, saving, error, removeItem } = useWishlist();

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>
      <div className="account-section-title">
        <h1>Wishlist</h1>
        <p>{wishlist?.line_count || items.length} saved item{items.length === 1 ? "" : "s"}</p>
      </div>
      <Alert>{error}</Alert>
      {loading ? (
        <Spinner label="Loading wishlist" />
      ) : items.length ? (
        <div className="wishlist-grid">
          {items.map((item, index) => (
            <WishlistCard key={item.id || item.product_id} item={item} index={index} saving={saving} onRemove={removeItem} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <strong>No saved products</strong>
          <p>Tap the save icon on products you want to compare later.</p>
          <Link className="primary-button empty-state__action" to="/catalog">
            <MaterialIcon name="storefront" size={18} />
            Browse products
          </Link>
        </div>
      )}
    </section>
  );
}
