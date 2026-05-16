import { Link } from "react-router-dom";

import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function AccountDashboardPage() {
  const { user, logout, loading, resendEmailVerification } = useAuth();
  const name = user?.full_name || user?.first_name || user?.email || "Account";
  const emailVerified = Boolean(user?.email_verification?.is_verified);

  return (
    <section className="account-page">
      {!emailVerified ? (
        <Alert tone="warning">
          Please verify your email address to keep account security notifications active.
          <button className="inline-action-button" type="button" disabled={loading} onClick={() => void resendEmailVerification()}>
            Resend verification
          </button>
        </Alert>
      ) : null}

      <div className="account-hero surface-panel">
        <span className="account-avatar">{initials(name)}</span>
        <div>
          <p className="eyebrow">Account</p>
          <h1>{name}</h1>
          <p>{user?.email}</p>
        </div>
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
        <Link className="account-action-card" to="/account/addresses">
          <MaterialIcon name="location_on" size={24} />
          <strong>Addresses</strong>
          <span>Delivery and billing details</span>
        </Link>
        <Link className="account-action-card" to="/account/reviews">
          <MaterialIcon name="reviews" size={24} />
          <strong>Reviews</strong>
          <span>Your product feedback</span>
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
