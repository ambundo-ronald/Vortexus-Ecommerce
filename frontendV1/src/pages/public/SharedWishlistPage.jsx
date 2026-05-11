import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import WishlistCard from "../../components/wishlist/WishlistCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { wishlistApi } from "../../api/wishlist.api";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Could not load this wishlist.";
}

export default function SharedWishlistPage() {
  const { key } = useParams();
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    wishlistApi.shared(key)
      .then((payload) => {
        if (active) setWishlist(payload?.wishlist || null);
      })
      .catch((error) => {
        if (active) setError(messageFromError(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [key]);

  const items = wishlist?.items || [];

  return (
    <section className="account-page">
      <Link className="back-link" to="/catalog">
        <MaterialIcon name="arrow_back" size={18} /> Catalog
      </Link>
      <div className="account-section-title">
        <h1>{wishlist?.name || "Shared wishlist"}</h1>
        <p>{items.length} saved item{items.length === 1 ? "" : "s"}</p>
      </div>
      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading shared wishlist" /> : null}
      {!loading && items.length ? (
        <div className="wishlist-grid">
          {items.map((item) => (
            <WishlistCard key={item.id || item.product_id} item={item} />
          ))}
        </div>
      ) : null}
      {!loading && !items.length && !error ? (
        <div className="empty-state">
          <strong>No products in this wishlist</strong>
          <p>The shared list is empty now.</p>
        </div>
      ) : null}
    </section>
  );
}
