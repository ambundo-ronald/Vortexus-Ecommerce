import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import CategoryNav from "../catalog/CategoryNav.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import SearchBar from "../search/SearchBar.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCategories } from "../../hooks/useCategories";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";

const navItems = [
  { to: "/catalog", labelKey: "navigation.shop", icon: "shopping_bag" },
];

const accountMenuItems = [
  { to: "/account", labelKey: "account.myAccount", icon: "person" },
  { to: "/account/orders", labelKey: "account.orders", icon: "inventory_2" },
  { to: "/account/messages", labelKey: "account.inbox", icon: "mail" },
  { to: "/account/wishlist", labelKey: "account.wishlist", icon: "favorite" },
  { to: "/offers", labelKey: "account.vouchers", icon: "confirmation_number" },
];

const languages = [
  { code: "en", labelKey: "language.english" },
  { code: "sw", labelKey: "language.swahili" },
  { code: "fr", labelKey: "language.french" },
  { code: "ar", labelKey: "language.arabic" },
  { code: "hi", labelKey: "language.hindi" },
  { code: "zh", labelKey: "language.mandarin" },
];

export default function Navbar() {
  const { t, i18n } = useTranslation();
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
    ? { to: "/supplier", labelKey: "account.supplierPortal", icon: "storefront" }
    : { to: "/supplier/apply", labelKey: "account.sellWithUs", icon: "add_business" };

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
          <NavLink to="/" end className="brand-link" aria-label={t("homeLabel")}>
            <span className="brand-mark brand-mark--logo">
              <img src="/Reesolmart logo.png" alt="" />
            </span>
          </NavLink>

          <nav className="desktop-nav" aria-label={t("navigation.primary")}>
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className="nav-link">
                <MaterialIcon name={item.icon} size={19} />
                {t(item.labelKey)}
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
                  <span>{t("account.greeting", { name: accountLabel(user) })}</span>
                  <MaterialIcon name={accountMenuOpen ? "keyboard_arrow_up" : "keyboard_arrow_down"} size={18} />
                </button>
                {accountMenuOpen ? (
                  <div className="account-menu__dropdown" role="menu">
                    {accountMenuItems.map((item) => (
                      <NavLink className="account-menu__item" to={item.to} key={item.to} role="menuitem" onClick={() => setAccountMenuOpen(false)}>
                        <MaterialIcon name={item.icon} size={23} />
                        <span>{t(item.labelKey)}</span>
                      </NavLink>
                    ))}
                    <NavLink
                      className="account-menu__item"
                      to={supplierMenuItem.to}
                      role="menuitem"
                      onClick={() => setAccountMenuOpen(false)}
                    >
                      <MaterialIcon name={supplierMenuItem.icon} size={23} />
                      <span>{t(supplierMenuItem.labelKey)}</span>
                    </NavLink>
                    <button className="account-menu__logout" type="button" disabled={loading} onClick={() => void logout()}>
                      {t("account.logout")}
                    </button>
                  </div>
                ) : null}
              </div>
            ) : (
              <NavLink to="/login" className="nav-link">
                <MaterialIcon name="person" size={19} />
                {t("account.signIn")}
              </NavLink>
            )}
          </nav>

          <label className="language-selector">
            <span className="visually-hidden">{t("language.label")}</span>
            <MaterialIcon name="language" size={19} />
            <select
              value={i18n.resolvedLanguage || i18n.language}
              onChange={(event) => void i18n.changeLanguage(event.target.value)}
              aria-label={t("language.label")}
            >
              {languages.map((language) => (
                <option key={language.code} value={language.code}>
                  {t(language.labelKey)}
                </option>
              ))}
            </select>
          </label>

          <button type="button" className="header-action" onClick={openCartDrawer} aria-label={t("cart")}>
            <span className="header-action__icon">
              <MaterialIcon name="shopping_cart" size={19} />
              {itemCount > 0 ? <span className="header-action__badge">{itemCount}</span> : null}
            </span>
            <span>{t("cart")}</span>
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
