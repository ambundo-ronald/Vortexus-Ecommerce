import { NavLink } from "react-router-dom";
import { useEffect } from "react";

import Footer from "./Footer.jsx";
import Navbar from "./Navbar.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cart.store";

export default function PageWrapper({ children }) {
  const hydrateCart = useCartStore((state) => state.hydrate);
  const { user } = useAuth();
  const bottomItems = [
    { to: "/", label: "Home", icon: "home" },
    { to: "/catalog", label: "Shop", icon: "storefront" },
    { to: "/search", label: "Search", icon: "travel_explore" },
    { to: "/checkout/cart", label: "Cart", icon: "shopping_cart" },
    { to: user ? "/account" : "/login", label: user ? "Account" : "Sign in", icon: "person" }
  ];

  useEffect(() => {
    void hydrateCart();
  }, [hydrateCart]);

  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">{children}</main>
      <Footer />

      <nav className="bottom-nav" aria-label="Mobile primary">
        {bottomItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === "/"} aria-label={item.label}>
            <span className="bottom-nav__icon">
              <MaterialIcon name={item.icon} size={24} filled />
            </span>
            <span className="bottom-nav__label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
