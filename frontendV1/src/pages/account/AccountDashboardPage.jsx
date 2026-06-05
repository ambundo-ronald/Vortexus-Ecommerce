import { Link } from "react-router-dom";

import EmailVerificationNotice, { isEmailVerified } from "../../components/account/EmailVerificationNotice.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function AccountDashboardPage() {
  const { user, logout, loading } = useAuth();
  const name = user?.full_name || user?.first_name || user?.email || "Account";
  const emailVerified = isEmailVerified(user);

  return (
    <section className="account-page">
      <EmailVerificationNotice user={user} />

      <div className="account-hero surface-panel">
        <span className="account-avatar">{initials(name)}</span>
        <div>
          <p className="eyebrow">Account</p>
          <h1>{name}</h1>
          <p>{user?.email}</p>
        </div>
        <span className={`account-email-pill${emailVerified ? " is-verified" : ""}`}>
          <MaterialIcon name={emailVerified ? "verified" : "error"} size={16} />
          {emailVerified ? "Verified email" : "Email pending"}
        </span>
      </div>

      <div className="account-action-grid">
        <Link className="account-action-card" to="/account/orders">
          <MaterialIcon name="receipt_long" size={24} />
          <strong>Orders</strong>
          <span>View your order history</span>
        </Link>
        <Link className="account-action-card" to="/account/wishlist">
          <MaterialIcon name="favorite" size={24} />
          <strong>Wishlist</strong>
          <span>Saved products</span>
        </Link>
        <Link className="account-action-card" to="/account/profile">
          <MaterialIcon name="manage_accounts" size={24} />
          <strong>Profile</strong>
          <span>Contact and preferences</span>
        </Link>
        <Link className="account-action-card" to="/account/preferences">
          <MaterialIcon name="tune" size={24} />
          <strong>Preferences</strong>
          <span>Store communication settings</span>
        </Link>
        <Link className="account-action-card" to="/account/delete">
          <MaterialIcon name="person_remove" size={24} />
          <strong>Delete account</strong>
          <span>Deactivate your customer account</span>
        </Link>
        <Link className="account-action-card" to="/account/addresses">
          <MaterialIcon name="location_on" size={24} />
          <strong>Addresses</strong>
          <span>Delivery and billing details</span>
        </Link>
        <Link className="account-action-card" to="/account/recently-viewed">
          <MaterialIcon name="history" size={24} />
          <strong>Recently viewed</strong>
          <span>Products you checked lately</span>
        </Link>
        <Link className="account-action-card" to="/account/notifications">
          <MaterialIcon name="notifications" size={24} />
          <strong>Notifications</strong>
          <span>Inbox and archived messages</span>
        </Link>
        <Link className="account-action-card" to="/account/messages">
          <MaterialIcon name="mail" size={24} />
          <strong>Messages</strong>
          <span>Email history from the store</span>
        </Link>
        <Link className="account-action-card" to="/account/reviews">
          <MaterialIcon name="reviews" size={24} />
          <strong>Reviews</strong>
          <span>Your product feedback</span>
        </Link>
        <Link className="account-action-card" to="/account/product-alerts">
          <MaterialIcon name="notifications_active" size={24} />
          <strong>Stock alerts</strong>
          <span>Availability notifications</span>
        </Link>
      </div>

      <button className="secondary-button account-logout" type="button" disabled={loading} onClick={() => void logout()}>
        <MaterialIcon name="logout" size={19} />
        Sign out
      </button>
    </section>
  );
}

function initials(value = "") {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  return (parts[0]?.[0] || "A") + (parts[1]?.[0] || "");
}
