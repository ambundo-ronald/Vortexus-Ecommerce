import { useLocation, useNavigate } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useUiStore } from "../../store/ui.store";
import { useWishlistStore } from "../../store/wishlist.store";

export default function WishlistButton({ productId, productTitle = "product", variant = "icon" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const inWishlist = useWishlistStore((state) => Boolean(state.statusByProductId[productId]));
  const saving = useWishlistStore((state) => Boolean(state.savingIds[productId]));
  const toggle = useWishlistStore((state) => state.toggle);
  const notify = useUiStore((state) => state.notify);

  async function handleClick(event) {
    event.preventDefault();
    event.stopPropagation();
    if (!user) {
      notify({ tone: "warning", title: "Sign in required", message: "Sign in to save products.", icon: "person" });
      navigate("/login", { state: { from: location } });
      return;
    }
    try {
      await toggle(productId);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  const label = inWishlist ? `Remove ${productTitle} from wishlist` : `Save ${productTitle}`;
  const className = variant === "detail" ? "wishlist-detail-button" : "wishlist-icon-button";

  return (
    <button className={`${className} ${inWishlist ? "active" : ""}`} type="button" disabled={saving} onClick={handleClick} aria-label={label}>
      <MaterialIcon name={inWishlist ? "favorite" : "favorite_border"} size={variant === "detail" ? 20 : 19} />
      {variant === "detail" ? <span>{inWishlist ? "Saved" : "Save"}</span> : null}
    </button>
  );
}
