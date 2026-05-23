import { useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function ProductAlertForm({ defaultEmail = "", loading = false, onSubmit }) {
  const [email, setEmail] = useState(defaultEmail);

  function submit(event) {
    event.preventDefault();
    onSubmit?.({ email: email.trim() });
  }

  return (
    <form className="product-alert-panel" onSubmit={submit}>
      <div className="product-alert-panel__head">
        <span><MaterialIcon name="notifications_active" size={21} /></span>
        <div>
          <h2>Notify me when available</h2>
          <p>We will tell you when this product is back in stock.</p>
        </div>
      </div>
      <div className="product-alert-panel__form">
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
        />
        <button className="primary-button" type="submit" disabled={loading}>
          <MaterialIcon name="notifications" size={18} />
          {loading ? "Saving..." : "Create alert"}
        </button>
      </div>
    </form>
  );
}
