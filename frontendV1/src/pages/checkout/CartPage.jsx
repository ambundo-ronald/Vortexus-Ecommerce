import CartEmpty from "../../components/cart/CartEmpty.jsx";
import CartItem from "../../components/cart/CartItem.jsx";
import CartSummary from "../../components/cart/CartSummary.jsx";
import Alert from "../../components/ui/Alert.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCart } from "../../hooks/useCart";

export default function CartPage() {
  const { basket, loading, error } = useCart();
  const lines = basket.lines || [];

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
    </>
  );
}
