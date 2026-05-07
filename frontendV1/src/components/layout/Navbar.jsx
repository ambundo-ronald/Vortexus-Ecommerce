import { NavLink, useLocation, useSearchParams } from "react-router-dom";

import CategoryNav from "../catalog/CategoryNav.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import SearchBar from "../search/SearchBar.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCategories } from "../../hooks/useCategories";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";

const navItems = [
  { to: "/", label: "Home", icon: "home" },
  { to: "/catalog", label: "Shop", icon: "storefront" },
];

export default function Navbar() {
  const itemCount = useCartStore((state) => state.basket.item_count || 0);
  const openCartDrawer = useUiStore((state) => state.openCartDrawer);
  const openWishlistDrawer = useUiStore((state) => state.openWishlistDrawer);
  const { user, logout, loading } = useAuth();
  const { categories } = useCategories();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const categoryMatch = location.pathname.match(/^\/catalog\/category\/([^/]+)/);
  const activeCategory = searchParams.get("category") || (categoryMatch ? decodeURIComponent(categoryMatch[1]) : "");
  const searchValue = searchParams.get("q") || "";
  const showCatalogTools = !location.pathname.startsWith("/account") && !location.pathname.startsWith("/admin") && !location.pathname.startsWith("/supplier");
  const showCategoryNavigation = location.pathname.startsWith("/catalog");

  return (
    <>
      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to="/" end className="brand-link" aria-label="Vortexus home">
            <span className="brand-mark">VX</span>
            <span className="brand-copy">
              <strong>Vortexus</strong>
              <span>Water projects and supplies</span>
            </span>
          </NavLink>

          <nav className="desktop-nav" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className="nav-link">
                <MaterialIcon name={item.icon} size={19} />
                {item.label}
              </NavLink>
            ))}
            <NavLink to={user ? "/account" : "/login"} className="nav-link">
              <MaterialIcon name="person" size={19} />
              {user ? accountLabel(user) : "Sign in"}
            </NavLink>
          </nav>

          {user ? (
            <button className="header-action" type="button" onClick={openWishlistDrawer}>
              <MaterialIcon name="favorite" size={20} />
              <span>Wishlist</span>
            </button>
          ) : null}
          <button type="button" className="header-action" onClick={openCartDrawer}>
            <MaterialIcon name="shopping_cart" size={20} />
            <span>Cart {itemCount}</span>
          </button>
          {user ? (
            <button className="notification-action" type="button" aria-label="Sign out" disabled={loading} onClick={() => void logout()}>
              <MaterialIcon name="logout" size={25} />
            </button>
          ) : (
            <NavLink className="notification-action" to="/login" aria-label="Sign in">
              <MaterialIcon name="person" size={27} />
            </NavLink>
          )}
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
      {showCategoryNavigation ? <CategoryNav categories={categories} activeCategory={activeCategory} variant="mobile" /> : null}
    </>
  );
}

function accountLabel(user) {
  return user?.first_name || user?.full_name || "Account";
}
