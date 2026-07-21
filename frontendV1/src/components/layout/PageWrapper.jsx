import { NavLink } from "react-router-dom";
import { useEffect } from "react";

import Footer from "./Footer.jsx";
import Navbar from "./Navbar.jsx";
import CartDrawer from "../cart/CartDrawer.jsx";
import RouteRobotsPolicy from "../seo/RouteRobotsPolicy.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import ToastViewport from "../ui/Toast.jsx";
import WishlistDrawer from "../wishlist/WishlistDrawer.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cart.store";

export default function PageWrapper({ children }) {
  const hydrateCart = useCartStore((state) => state.hydrate);
  const itemCount = useCartStore((state) => state.basket.item_count || 0);
  const { user } = useAuth();
  const bottomItems = [
    { to: "/", label: "Home", icon: "home" },
    { to: "/catalog", label: "Shop", icon: "shopping_bag" },
    { to: "/catalog", label: "Categories", icon: "category" },
    { to: "/checkout/cart", label: "Cart", icon: "shopping_cart" },
    { to: user ? "/account" : "/login", label: user ? "Account" : "Sign in", icon: "person" }
  ];

  useEffect(() => {
    void hydrateCart();
  }, [hydrateCart]);

  return (
    <div className="app-shell">
      <RouteRobotsPolicy />
      <Navbar />
      <main className="app-main">{children}</main>
      <Footer />
      <CartDrawer />
      <WishlistDrawer />
      <ToastViewport />

      <nav className="bottom-nav" aria-label="Mobile primary">
        {bottomItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === "/"} aria-label={item.label}>
            <span className="bottom-nav__icon">
              <MaterialIcon name={item.icon} size={24} filled />
              {item.to === "/checkout/cart" && itemCount > 0 ? (
                <span className="bottom-nav__badge">{itemCount}</span>
              ) : null}
            </span>
            <span className="bottom-nav__label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
