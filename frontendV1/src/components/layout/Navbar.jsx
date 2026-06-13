import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useSearchParams } from "react-router-dom";

import CategoryNav from "../catalog/CategoryNav.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import SearchBar from "../search/SearchBar.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCategories } from "../../hooks/useCategories";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";

const navItems = [
  { to: "/catalog", label: "Shop", icon: "shopping_bag" },
];

const accountMenuItems = [
  { to: "/account", label: "My Account", icon: "person" },
  { to: "/account/orders", label: "Orders", icon: "inventory_2" },
  { to: "/account/messages", label: "Inbox", icon: "mail" },
  { to: "/account/wishlist", label: "Wishlist", icon: "favorite" },
  { to: "/offers", label: "Vouchers", icon: "confirmation_number" },
];

export default function Navbar() {
  const itemCount = useCartStore((state) => state.basket.item_count || 0);
  const openCartDrawer = useUiStore((state) => state.openCartDrawer);
  const { user, logout, loading } = useAuth();
  const { categories } = useCategories();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef(null);
  const categoryMatch = location.pathname.match(/^\/catalog\/category\/([^/]+)/);
  const activeCategory = searchParams.get("category") || (categoryMatch ? decodeURIComponent(categoryMatch[1]) : "");
  const searchValue = searchParams.get("q") || "";
  const showCatalogTools = !location.pathname.startsWith("/account") && !location.pathname.startsWith("/admin") && !location.pathname.startsWith("/supplier");
  const showCategoryNavigation = location.pathname.startsWith("/catalog");
  const supplierMenuItem = user?.supplier?.is_supplier
    ? { to: "/supplier", label: "Supplier portal", icon: "storefront" }
    : { to: "/supplier/apply", label: "Sell with us", icon: "add_business" };

  useEffect(() => {
    setAccountMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!accountMenuOpen) return undefined;

    function handlePointerDown(event) {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target)) {
        setAccountMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [accountMenuOpen]);

  return (
    <>
      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to="/" end className="brand-link" aria-label="Vortexus home">
            <span className="brand-mark">VX</span>
            <span className="brand-copy">
              <strong>Vortexus</strong>
              <span>industrial marketplace</span>
            </span>
          </NavLink>

          <nav className="desktop-nav" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className="nav-link">
                <MaterialIcon name={item.icon} size={19} />
                {item.label}
              </NavLink>
            ))}
            {user ? (
              <div className="account-menu" ref={accountMenuRef}>
                <button
                  className={`account-menu__trigger${accountMenuOpen ? " is-open" : ""}`}
                  type="button"
                  aria-haspopup="menu"
                  aria-expanded={accountMenuOpen}
                  onClick={() => setAccountMenuOpen((current) => !current)}
                >
                  <MaterialIcon name="person_check" size={19} />
                  <span>Hi, {accountLabel(user)}</span>
                  <MaterialIcon name={accountMenuOpen ? "keyboard_arrow_up" : "keyboard_arrow_down"} size={18} />
                </button>
                {accountMenuOpen ? (
                  <div className="account-menu__dropdown" role="menu">
                    {accountMenuItems.map((item) => (
                      <NavLink className="account-menu__item" to={item.to} key={item.to} role="menuitem" onClick={() => setAccountMenuOpen(false)}>
                        <MaterialIcon name={item.icon} size={23} />
                        <span>{item.label}</span>
                      </NavLink>
                    ))}
                    <NavLink
                      className="account-menu__item"
                      to={supplierMenuItem.to}
                      role="menuitem"
                      onClick={() => setAccountMenuOpen(false)}
                    >
                      <MaterialIcon name={supplierMenuItem.icon} size={23} />
                      <span>{supplierMenuItem.label}</span>
                    </NavLink>
                    <button className="account-menu__logout" type="button" disabled={loading} onClick={() => void logout()}>
                      Logout
                    </button>
                  </div>
                ) : null}
              </div>
            ) : (
              <NavLink to="/login" className="nav-link">
                <MaterialIcon name="person" size={19} />
                Sign in
              </NavLink>
            )}
          </nav>

          <button type="button" className="header-action" onClick={openCartDrawer}>
            <span className="header-action__icon">
              <MaterialIcon name="shopping_cart" size={19} />
              {itemCount > 0 ? <span className="header-action__badge">{itemCount}</span> : null}
            </span>
            <span>Cart</span>
          </button>
        </div>
        {showCatalogTools ? (
          <div className="app-header__tools">
            <div className="header-search-row">
              <SearchBar initialValue={searchValue} compact />
            </div>
            {showCategoryNavigation ? <CategoryNav categories={categories} activeCategory={activeCategory} /> : null}
          </div>
        ) : null}
      </header>
    </>
  );
}

function accountLabel(user) {
  return user?.first_name || user?.full_name || user?.username || "user";
}
