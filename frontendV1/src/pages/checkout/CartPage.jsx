import { useEffect } from "react";

import CartEmpty from "../../components/cart/CartEmpty.jsx";
import CartItem from "../../components/cart/CartItem.jsx";
import CartSummary from "../../components/cart/CartSummary.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCart } from "../../hooks/useCart";
import { useCartStore } from "../../store/cart.store";
import { formatCurrency } from "../../utils/currency";
import { productImageUrl } from "../../utils/productImages";

export default function CartPage() {
  const { basket, loading, error } = useCart();
  const savedItems = useCartStore((state) => state.savedItems);
  const savedLoading = useCartStore((state) => state.savedLoading);
  const loadSavedItems = useCartStore((state) => state.loadSavedItems);
  const moveSavedToCart = useCartStore((state) => state.moveSavedToCart);
  const removeSavedItem = useCartStore((state) => state.removeSavedItem);
  const lines = basket.lines || [];

  useEffect(() => {
    void loadSavedItems();
  }, [loadSavedItems]);

  return (
    <>
      <section className="surface-panel page-intro cart-intro">
        <div>
          <p className="eyebrow">Cart</p>
          <h1>Your cart</h1>
          <p>{basket.item_count || 0} item{basket.item_count === 1 ? "" : "s"}</p>
        </div>
      </section>

      <Alert>{error}</Alert>
      {loading && !lines.length ? <Spinner label="Loading cart" /> : null}

      {!loading && !lines.length ? (
        <CartEmpty />
      ) : (
        <section className="cart-layout">
          <div className="cart-lines">
            {lines.map((line) => (
              <CartItem key={line.id} line={line} />
            ))}
          </div>
          <CartSummary basket={basket} />
        </section>
      )}

      {savedLoading ? <Spinner label="Loading saved items" /> : null}
      {savedItems.length ? (
        <section className="content-section saved-items-section">
          <div className="section-heading">
            <h2>Saved for later</h2>
            <span>{savedItems.length}</span>
          </div>
          <div className="saved-items-grid">
            {savedItems.map((item) => (
              <SavedCartItem
                key={item.id}
                item={item}
                disabled={loading || savedLoading}
                onMove={async () => {
                  try {
                    await moveSavedToCart(item.id);
                  } catch {
                    // Store notification already shows the failed action.
                  }
                }}
                onRemove={async () => {
                  try {
                    await removeSavedItem(item.id);
                  } catch {
                    // Store notification already shows the failed action.
                  }
                }}
              />
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}

function SavedCartItem({ item, disabled, onMove, onRemove }) {
  const product = item.product || item.wishlist_item?.product || {};
  const options = item.options || item.wishlist_item?.options || [];
  const image = productImageUrl(product);
  return (
    <article className="saved-cart-item">
      <div className="saved-cart-item__media">
        {image ? <img src={image} alt={product.title || "Product"} /> : <MaterialIcon name="inventory_2" size={26} />}
      </div>
      <div>
        <strong>{product.title || "Saved product"}</strong>
        {options.length ? (
          <ul className="cart-item__options">
            {options.map((option) => (
              <li key={option.id || option.code}>
                <span>{option.name || option.code}</span>
                <strong>{option.value}</strong>
              </li>
            ))}
          </ul>
        ) : null}
        <span>{formatCurrency(product.price, product.currency)}</span>
      </div>
      <div className="saved-cart-item__actions">
        <button className="secondary-button" type="button" disabled={disabled} onClick={() => void onMove()}>
          <MaterialIcon name="add_shopping_cart" size={18} />
          Move
        </button>
        <button className="danger-link" type="button" disabled={disabled} onClick={() => void onRemove()} aria-label="Remove saved item">
          <MaterialIcon name="delete" size={18} />
        </button>
      </div>
    </article>
  );
}
