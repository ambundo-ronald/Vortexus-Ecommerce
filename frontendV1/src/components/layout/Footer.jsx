import { NavLink } from "react-router-dom";
import { FaFacebookF, FaInstagram, FaLinkedinIn } from "react-icons/fa";
import { FaXTwitter } from "react-icons/fa6";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import "./StoreFooter.css";

const shopLinks = [
  { to: "/catalog", label: "Shop", icon: "shopping_bag" },
  { to: "/search", label: "Search", icon: "travel_explore" },
  { to: "/offers", label: "Offers", icon: "local_offer" },
  { to: "/quote", label: "Quote", icon: "request_quote" },
  { to: "/catalog?sort_by=newest", label: "New arrivals", icon: "new_releases" },
];

const supportLinks = [
  { to: "/orders/track", label: "Track order", icon: "local_shipping" },
  { to: "/quote", label: "Support", icon: "engineering" },
  { to: "/account/product-alerts", label: "Alerts", icon: "notifications_active" },
  { to: "/account/recently-viewed", label: "Recently viewed", icon: "history" },
  { to: "/account/messages", label: "Inbox", icon: "mail" },
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
  { to: "/offers", label: "Offers", icon: "sell" },
  { to: "/account/reviews", label: "Reviews", icon: "star" },
  { href: "mailto:support@reesolmart.com", label: "Email support", icon: "alternate_email" },
];

const quickActions = [
  { to: "/catalog", label: "Shop", icon: "shopping_bag" },
  { to: "/quote", label: "Quote", icon: "request_quote" },
  { to: "/orders/track", label: "Track", icon: "local_shipping" },
  { to: "/account/wishlist", label: "Wishlist", icon: "favorite" },
  { to: "/account/messages", label: "Inbox", icon: "forum" },
  { href: "mailto:support@reesolmart.com", label: "Email", icon: "mail" },
];

const socialLinks = [
  { href: "https://x.com/Reesolmart", label: "X", Icon: FaXTwitter },
  { href: "https://www.instagram.com/reesolmart/", label: "Instagram", Icon: FaInstagram },
  { href: "https://www.linkedin.com/in/reesol-mart-03b3a0420/", label: "LinkedIn", Icon: FaLinkedinIn },
  { href: "https://www.facebook.com/people/Reesolmart/61591495931916/", label: "Facebook", Icon: FaFacebookF },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="store-footer app-footer">
      <div className="store-footer__inner">
        <NavLink to="/" className="store-footer__logo" aria-label="Reesolmart home">
          <span className="brand-mark brand-mark--logo">
            <img src="/Reesolmart logo.png" alt="" />
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
                <span>Nairobi, Kenya</span>
              </span>
              <a href="mailto:support@reesolmart.com">
                <MaterialIcon name="mail" size={20} />
                <span>support@reesolmart.com</span>
              </a>
              <NavLink to="/quote">
                <MaterialIcon name="chat" size={20} />
                <span>Request help</span>
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

        <section className="store-footer__socials" aria-label="Reesolmart social links">
          {socialLinks.map(({ href, label, Icon }) => (
            <a key={href} href={href} target="_blank" rel="noreferrer" aria-label={`Reesolmart on ${label}`}>
              <Icon aria-hidden="true" />
              <span>{label}</span>
            </a>
          ))}
        </section>

        <div className="store-footer__bottom">
          <span>© {year} Reesolmart.</span>
          <span className="store-footer__legal">
            <NavLink to="/offers">Offers</NavLink>
            <NavLink to="/quote">Quote</NavLink>
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
