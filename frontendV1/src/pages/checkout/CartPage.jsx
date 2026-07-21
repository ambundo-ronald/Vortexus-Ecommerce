import { useEffect, useRef } from "react";

import CartEmpty from "../../components/cart/CartEmpty.jsx";
import CartItem from "../../components/cart/CartItem.jsx";
import CartSummary from "../../components/cart/CartSummary.jsx";
import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCart } from "../../hooks/useCart";
import { useCartStore } from "../../store/cart.store";
import { productInitials, productPrice, productSku, productTitle, stockTone } from "../../utils/productDisplay";
import { productImageAlt, productImageUrl } from "../../utils/productImages";
import "./CartPage.css";

export default function CartPage() {
  const { basket, loading, error } = useCart();
  const savedItems = useCartStore((state) => state.savedItems);
  const savedLoading = useCartStore((state) => state.savedLoading);
  const loadSavedItems = useCartStore((state) => state.loadSavedItems);
  const moveSavedToCart = useCartStore((state) => state.moveSavedToCart);
  const removeSavedItem = useCartStore((state) => state.removeSavedItem);
  const clearCart = useCartStore((state) => state.clearCart);
  const lines = basket.lines || [];
  const itemCount = basket.item_count || lines.reduce((total, line) => total + Number(line.quantity || 0), 0);
  const itemLabel = itemCount === 1 ? "Item" : "Items";
  const savedItemsRef = useRef(null);

  useEffect(() => {
    void loadSavedItems();
  }, [loadSavedItems]);

  function scrollSavedItems() {
    savedItemsRef.current?.scrollBy({
      left: Math.max(280, savedItemsRef.current.clientWidth * 0.75),
      behavior: "smooth",
    });
  }

  async function handleClearCart() {
    try {
      await clearCart();
    } catch {
      // The cart store already shows a notification for failed clearing.
    }
  }

  return (
    <div className="cart-page">
      <CheckoutStepper current="cart" basket={basket} />
      <Alert>{error}</Alert>
      {loading && !lines.length ? <Spinner label="Loading cart" /> : null}

      {!loading && !lines.length ? (
        <CartEmpty />
      ) : (
        <section className="cart-layout">
          <section className="cart-products-panel" aria-labelledby="cart-page-title">
            <div className="cart-products-panel__head">
              <div>
                <h1 id="cart-page-title">Your cart</h1>
              </div>
              <div className="cart-products-panel__actions">
                <span className="cart-products-panel__count">
                  <MaterialIcon name="shopping_cart" size={18} />
                  {itemCount} {itemLabel}
                </span>
                <button className="cart-products-panel__clear" type="button" disabled={loading} onClick={() => void handleClearCart()}>
                  Clear cart
                </button>
              </div>
            </div>
            <div className="cart-table-head" aria-hidden="true">
              <span>Product</span>
              <span>Price</span>
              <span>Qty</span>
              <span>Total</span>
              <span></span>
            </div>
            <div className="cart-lines">
              {lines.map((line) => (
                <CartItem key={line.id} line={line} />
              ))}
            </div>
          </section>
          <CartSummary basket={basket} />
        </section>
      )}

      {savedLoading ? <Spinner label="Loading saved items" /> : null}
      {savedItems.length ? (
        <section className="content-section saved-items-section">
          <div className="section-heading">
            <h2>Saved for later</h2>
            <span>
              {savedItems.length} {savedItems.length === 1 ? "Item" : "Items"}
            </span>
          </div>
          <div className="saved-items-grid" ref={savedItemsRef}>
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
          {savedItems.length > 2 ? (
            <button className="saved-items-next" type="button" onClick={scrollSavedItems} aria-label="Show more saved items">
              <MaterialIcon name="chevron_right" size={24} />
            </button>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function SavedCartItem({ item, disabled, onMove, onRemove }) {
  const product = item.product || item.wishlist_item?.product || {};
  const options = item.options || item.wishlist_item?.options || [];
  const image = productImageUrl({ ...item, ...product, product });
  const title = productTitle({ ...item, product }, "Saved product");
  const imageAlt = productImageAlt({ ...item, ...product, product }, title);
  const sku = productSku({ ...item, product }, product.slug || "Saved product");
  const price = productPrice(product);
  const stock = stockTone(product);

  return (
    <article className="saved-cart-item">
      <div className="saved-cart-item__media">
        {image ? (
          <img
            src={image}
            alt={imageAlt}
            loading="lazy"
            decoding="async"
            width="160"
            height="160"
          />
        ) : <span>{productInitials(title)}</span>}
      </div>
      <div className="saved-cart-item__body">
        <strong>{title}</strong>
        <span className="saved-cart-item__sku">SKU: {sku}</span>
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
        <span className="saved-cart-item__price">{price.label || "Quote on request"}</span>
        <span className={`saved-cart-item__stock ${stock.isAvailable ? "is-in-stock" : "is-sold-out"}`}>
          <MaterialIcon name={stock.isAvailable ? "check_circle" : "block"} size={15} />
          {stock.label}
        </span>
      </div>
      <div className="saved-cart-item__actions">
        <button className="secondary-button" type="button" disabled={disabled} onClick={() => void onMove()}>
          <MaterialIcon name="add_shopping_cart" size={18} />
          Move to cart
        </button>
        <button className="danger-link" type="button" disabled={disabled} onClick={() => void onRemove()} aria-label="Remove saved item">
          <MaterialIcon name="delete" size={18} />
        </button>
      </div>
    </article>
  );
}
