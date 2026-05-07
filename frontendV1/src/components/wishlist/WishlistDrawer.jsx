import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import WishlistCard from "./WishlistCard.jsx";
import Alert from "../ui/Alert.jsx";
import { useWishlist } from "../../hooks/useWishlist";
import { useUiStore } from "../../store/ui.store";

export default function WishlistDrawer() {
  const open = useUiStore((state) => state.wishlistDrawerOpen);
  const close = useUiStore((state) => state.closeWishlistDrawer);
  const { items, error, saving, removeItem } = useWishlist({ auto: open });

  return (
    <div className={`drawer-shell ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="drawer-shade" type="button" onClick={close} aria-label="Close wishlist" />
      <aside className="drawer-panel" aria-label="Wishlist drawer">
        <div className="drawer-head">
          <strong>Wishlist</strong>
          <button type="button" onClick={close} aria-label="Close wishlist">
            <MaterialIcon name="close" size={22} />
          </button>
        </div>
        <Alert>{error}</Alert>
        <div className="drawer-scroll wishlist-drawer-list">
          {items.length ? items.map((item) => (
            <WishlistCard key={item.id || item.product?.id} item={item} saving={saving} onRemove={removeItem} />
          )) : (
            <div className="empty-state">
              <strong>No saved products</strong>
              <p>Save products with the heart icon.</p>
            </div>
          )}
        </div>
        <div className="drawer-footer">
          <Link className="primary-button" to="/account/wishlist" onClick={close}>
            <MaterialIcon name="favorite" size={19} />
            Open wishlist
          </Link>
        </div>
      </aside>
    </div>
  );
}
