import { NavLink } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import "./StoreFooter.css";

const shopLinks = [
  { to: "/catalog", label: "Shop products", icon: "shopping_bag" },
  { to: "/search", label: "Search products", icon: "travel_explore" },
  { to: "/offers", label: "Offers and deals", icon: "local_offer" },
  { to: "/quote", label: "Request a quote", icon: "request_quote" },
  { to: "/catalog?sort_by=newest", label: "New arrivals", icon: "new_releases" },
  { to: "/catalog?in_stock=true", label: "In stock now", icon: "inventory" },
];

const supportLinks = [
  { to: "/orders/track", label: "Track order", icon: "local_shipping" },
  { to: "/quote", label: "Project support", icon: "engineering" },
  { to: "/account/product-alerts", label: "Product alerts", icon: "notifications_active" },
  { to: "/account/recently-viewed", label: "Recently viewed", icon: "history" },
  { to: "/account/messages", label: "Inbox", icon: "mail" },
  { to: "/account/notifications", label: "Notifications", icon: "campaign" },
];

const accountLinks = [
  { to: "/account", label: "My account", icon: "person" },
  { to: "/account/orders", label: "Orders", icon: "receipt_long" },
  { to: "/account/wishlist", label: "Wishlist", icon: "favorite" },
  { to: "/login", label: "Sign in", icon: "login" },
  { to: "/register", label: "Create account", icon: "person_add" },
  { to: "/account/addresses", label: "Address book", icon: "location_on" },
  { to: "/account/preferences", label: "Preferences", icon: "tune" },
];

const companyLinks = [
  { to: "/", label: "Home", icon: "home" },
  { to: "/offers", label: "Campaigns", icon: "sell" },
  { to: "/account/reviews", label: "Reviews", icon: "star" },
  { to: "/account/delete", label: "Account controls", icon: "manage_accounts" },
  { href: "mailto:support@vortexus.local", label: "Email support", icon: "alternate_email" },
];

const quickActions = [
  { to: "/catalog", label: "Shop", icon: "shopping_bag" },
  { to: "/quote", label: "Quote", icon: "request_quote" },
  { to: "/orders/track", label: "Track", icon: "local_shipping" },
  { to: "/account/wishlist", label: "Wishlist", icon: "favorite" },
  { to: "/account/messages", label: "Inbox", icon: "forum" },
  { href: "mailto:support@vortexus.local", label: "Email", icon: "mail" },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="store-footer app-footer">
      <div className="store-footer__inner">
        <NavLink to="/" className="store-footer__logo" aria-label="Vortexus home">
          <span className="brand-mark">VX</span>
          <span>
            <strong>Vortexus</strong>
            <small>Industrial marketplace</small>
          </span>
        </NavLink>

        <nav className="store-footer__nav" aria-label="Footer navigation">
          <FooterGroup title="Shop" links={shopLinks} />
          <FooterGroup title="Support" links={supportLinks} />
          <FooterGroup title="Account" links={accountLinks} />
          <FooterGroup title="Company" links={companyLinks} />

          <section className="store-footer__contact" aria-label="Contact us">
            <h2>Contact Us</h2>
            <div className="store-footer__contact-list">
              <span>
                <MaterialIcon name="location_on" size={20} />
                <span>Nairobi, Kenya<br />Serving water projects and industrial supply teams</span>
              </span>
              <a href="mailto:support@vortexus.local">
                <MaterialIcon name="mail" size={20} />
                <span>support@vortexus.local</span>
              </a>
              <NavLink to="/quote">
                <MaterialIcon name="chat" size={20} />
                <span>Request product or project help</span>
              </NavLink>
            </div>
          </section>
        </nav>

        <section className="store-footer__quick-actions" aria-label="Quick footer actions">
          <strong>Quick actions</strong>
          <div>
            {quickActions.map((link) => (
              <FooterIconLink link={link} key={link.to || link.href} />
            ))}
          </div>
        </section>

        <div className="store-footer__bottom">
          <span>© {year} Vortexus Industrial Marketplace.</span>
          <span>Built for mobile purchasing, quotes, checkout, order tracking, and account service.</span>
          <span className="store-footer__legal">
            <NavLink to="/offers">Offers</NavLink>
            <NavLink to="/quote">Quote support</NavLink>
            <NavLink to="/orders/track">Track order</NavLink>
          </span>
        </div>
      </div>
    </footer>
  );
}

function FooterGroup({ title, links }) {
  return (
    <section className="store-footer__group">
      <h2>{title}</h2>
      <ul className="store-footer__links">
        {links.map((link) => (
          <li key={link.to || link.href}>
            <FooterLink link={link} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function FooterLink({ link }) {
  const content = (
    <>
      <MaterialIcon name={link.icon} size={18} />
      <span>{link.label}</span>
    </>
  );

  if (link.href) {
    return <a href={link.href}>{content}</a>;
  }

  return <NavLink to={link.to}>{content}</NavLink>;
}

function FooterIconLink({ link }) {
  const content = (
    <>
      <MaterialIcon name={link.icon} size={20} />
      <span>{link.label}</span>
    </>
  );

  if (link.href) {
    return <a href={link.href}>{content}</a>;
  }

  return <NavLink to={link.to}>{content}</NavLink>;
}
