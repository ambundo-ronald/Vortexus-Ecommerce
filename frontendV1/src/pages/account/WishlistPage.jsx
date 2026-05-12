import { useState } from "react";
import { Link } from "react-router-dom";

import WishlistCard from "../../components/wishlist/WishlistCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useWishlist } from "../../hooks/useWishlist";

export default function WishlistPage() {
  const { wishlist, items, loading, saving, error, removeItem, shareWishlist } = useWishlist();
  const [shareLink, setShareLink] = useState("");

  async function handleShare(regenerate = false) {
    const payload = await shareWishlist({ regenerate });
    if (!payload?.share_path) return;
    const nextLink = `${window.location.origin}${payload.share_path.replace(/^\/api\/v1/, "")}`;
    setShareLink(nextLink);
    try {
      await navigator.clipboard.writeText(nextLink);
    } catch {
      // Clipboard may be blocked outside secure contexts; the link stays visible.
    }
  }

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>
      <div className="account-section-title">
        <h1>Wishlist</h1>
        <p>{wishlist?.line_count || items.length} saved item{items.length === 1 ? "" : "s"}</p>
      </div>
      {wishlist?.id ? (
        <div className="wishlist-share-panel surface-panel">
          <div>
            <strong>Share wishlist</strong>
            <span>Create a link that opens this saved list.</span>
          </div>
          <button className="secondary-button" type="button" disabled={saving} onClick={() => void handleShare(false)}>
            <MaterialIcon name="ios_share" size={18} />
            Share
          </button>
          {shareLink ? (
            <>
              <input value={shareLink} readOnly aria-label="Wishlist share link" />
              <button className="secondary-button" type="button" disabled={saving} onClick={() => void handleShare(true)}>
                <MaterialIcon name="refresh" size={18} />
                Regenerate
              </button>
            </>
          ) : null}
        </div>
      ) : null}
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
