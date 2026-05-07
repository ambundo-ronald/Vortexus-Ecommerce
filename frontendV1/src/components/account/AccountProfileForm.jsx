import { useState } from "react";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function AccountProfileForm({ user, loading = false, error = "", onSubmit }) {
  const [form, setForm] = useState(() => ({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    email: user?.email || "",
    phone: user?.phone || "",
    company: user?.company || "",
    country_code: user?.country_code || "KE",
    preferred_currency: user?.preferred_currency || "",
    receive_order_updates: user?.settings?.receive_order_updates ?? true,
    receive_marketing_emails: user?.settings?.receive_marketing_emails ?? false
  }));

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({
      ...form,
      country_code: form.country_code.toUpperCase(),
      preferred_currency: form.preferred_currency.toUpperCase()
    });
  }

  return (
    <form className="auth-card account-form" onSubmit={handleSubmit}>
      <div className="auth-card__head">
        <span><MaterialIcon name="manage_accounts" size={24} /></span>
        <div>
          <h1>Profile</h1>
          <p>Keep your contact details current.</p>
        </div>
      </div>

      <Alert>{error}</Alert>

      <div className="form-grid two">
        <label>
          <span>First name</span>
          <input name="first_name" value={form.first_name} onChange={updateField} />
        </label>
        <label>
          <span>Last name</span>
          <input name="last_name" value={form.last_name} onChange={updateField} />
        </label>
      </div>

      <label>
        <span>Email</span>
        <input type="email" name="email" value={form.email} onChange={updateField} required />
      </label>

      <div className="form-grid two">
        <label>
          <span>Phone</span>
          <input name="phone" value={form.phone} onChange={updateField} />
        </label>
        <label>
          <span>Company</span>
          <input name="company" value={form.company} onChange={updateField} />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Country</span>
          <input name="country_code" value={form.country_code} onChange={updateField} maxLength="2" />
        </label>
        <label>
          <span>Currency</span>
          <input name="preferred_currency" value={form.preferred_currency} onChange={updateField} maxLength="3" placeholder={user?.display_currency || "KES"} />
        </label>
      </div>

      <label className="auth-check">
        <input type="checkbox" name="receive_order_updates" checked={form.receive_order_updates} onChange={updateField} />
        <span>Send me order updates</span>
      </label>

      <label className="auth-check">
        <input type="checkbox" name="receive_marketing_emails" checked={form.receive_marketing_emails} onChange={updateField} />
        <span>Send offers and product updates</span>
      </label>

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        <MaterialIcon name="save" size={19} />
        {loading ? "Saving..." : "Save profile"}
      </button>
    </form>
  );
}
