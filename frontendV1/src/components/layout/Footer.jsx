import { NavLink } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const shopLinks = [
  { to: "/catalog", label: "Shop products" },
  { to: "/offers", label: "Offers" },
  { to: "/quote", label: "Request quote" },
  { to: "/search", label: "Search" },
];

const supportLinks = [
  { to: "/orders/track", label: "Track order" },
  { to: "/account/orders", label: "Order history" },
  { to: "/account/wishlist", label: "Wishlist" },
  { to: "/account/product-alerts", label: "Product alerts" },
];

const accountLinks = [
  { to: "/login", label: "Sign in" },
  { to: "/register", label: "Create account" },
  { to: "/account/addresses", label: "Address book" },
  { to: "/account/preferences", label: "Preferences" },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="app-footer">
      <div className="app-footer__inner">
        <section className="footer-brand" aria-label="Vortexus footer">
          <NavLink to="/" className="footer-brand__logo" aria-label="Vortexus home">
            <span className="brand-mark">VX</span>
            <span>
              <strong>Vortexus</strong>
              <small>Water projects and supplies</small>
            </span>
          </NavLink>
          <p>
            Source pumps, water treatment systems, controls, spares, and project supplies with clear pricing and checkout.
          </p>
          <div className="footer-trust-row" aria-label="Store promises">
            <span>
              <MaterialIcon name="verified" size={18} filled />
              Genuine supplies
            </span>
            <span>
              <MaterialIcon name="local_shipping" size={18} />
              Dispatch support
            </span>
            <span>
              <MaterialIcon name="support_agent" size={18} />
              Project help
            </span>
          </div>
        </section>

        <nav className="footer-link-grid" aria-label="Footer navigation">
          <FooterGroup title="Shop" links={shopLinks} />
          <FooterGroup title="Support" links={supportLinks} />
          <FooterGroup title="Account" links={accountLinks} />
        </nav>

        <section className="footer-contact" aria-label="Contact and actions">
          <span className="footer-contact__eyebrow">Need project help?</span>
          <h2>Get the right equipment before checkout.</h2>
          <NavLink to="/quote" className="footer-cta">
            <MaterialIcon name="description" size={19} />
            Request a quote
          </NavLink>
          <div className="footer-socials" aria-label="Quick footer actions">
            <NavLink to="/quote" aria-label="Request quote">
              <MaterialIcon name="chat" size={19} />
            </NavLink>
            <a href="mailto:support@vortexus.local" aria-label="Email">
              <MaterialIcon name="mail" size={19} />
            </a>
            <NavLink to="/orders/track" aria-label="Track order">
              <MaterialIcon name="pin_drop" size={19} />
            </NavLink>
          </div>
        </section>

        <div className="footer-bottom">
          <span>© {year} Vortexus Industrial Marketplace.</span>
          <span>Built for mobile purchasing, quotes, checkout, and account service.</span>
        </div>
      </div>
    </footer>
  );
}

function FooterGroup({ title, links }) {
  return (
    <div className="footer-link-group">
      <h2>{title}</h2>
      <ul>
        {links.map((link) => (
          <li key={link.to}>
            <NavLink to={link.to}>{link.label}</NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
}
