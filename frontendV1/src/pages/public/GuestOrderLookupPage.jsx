import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import EmailTouchpointCard from "../../components/account/EmailTouchpointCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import "./guestOrder.css";

export default function GuestOrderLookupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ order_number: "", email: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.orders.guestLookup({
        order_number: form.order_number.trim(),
        email: form.email.trim()
      });
      navigate(`/orders/track/${encodeURIComponent(payload.order_number)}/${encodeURIComponent(payload.hash)}`);
    } catch (requestError) {
      const message = requestError?.normalized?.status === 404
        ? "No order matched those details. Check the order number and email."
        : normalizeApiError(requestError, "Could not find that order.").message;
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="guest-order-page">
      <form className="guest-order-card" onSubmit={submit}>
        <div className="guest-order-card__head">
          <span><MaterialIcon name="package_2" size={25} /></span>
          <div>
            <p className="eyebrow">Track order</p>
            <h1>Find your order</h1>
            <p>Use the order number and email used at checkout.</p>
          </div>
        </div>

        <Alert>{error}</Alert>

        <EmailTouchpointCard
          className="guest-order-email-card"
          eyebrow="Email lookup"
          icon="alternate_email"
          message="Use the same email address from checkout. Guest tracking links are private and expire after 30 days."
          title="Your order email unlocks tracking"
          tone="security"
        />

        <label>
          <span>Order number</span>
          <input name="order_number" value={form.order_number} onChange={updateField} placeholder="100013" autoComplete="off" required />
        </label>

        <label>
          <span>Email address</span>
          <input type="email" name="email" value={form.email} onChange={updateField} placeholder="you@example.com" autoComplete="email" required />
        </label>

        <button className="primary-button guest-order-card__submit" type="submit" disabled={loading}>
          <MaterialIcon name="search" size={19} />
          {loading ? "Checking..." : "Track order"}
        </button>

        <p className="guest-order-card__note">
          Have an account? <Link to="/account/orders">View order history</Link>
        </p>
      </form>
    </section>
  );
}
