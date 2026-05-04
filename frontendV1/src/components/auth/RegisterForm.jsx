import { useState } from "react";
import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";

const initialForm = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  country_code: "KE",
  password: "",
  password_confirm: "",
  receive_order_updates: true,
  receive_marketing_emails: false
};

export default function RegisterForm({ loading = false, error = "", onSubmit }) {
  const [form, setForm] = useState(initialForm);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({
      ...form,
      country_code: form.country_code.toUpperCase()
    });
  }

  return (
    <form className="auth-card" onSubmit={handleSubmit}>
      <div className="auth-card__head">
        <span><MaterialIcon name="person_add" size={24} /></span>
        <div>
          <h1>Create account</h1>
          <p>Track orders and checkout faster next time.</p>
        </div>
      </div>

      <Alert>{error}</Alert>

      <div className="form-grid two">
        <label>
          <span>First name</span>
          <input name="first_name" value={form.first_name} onChange={updateField} autoComplete="given-name" />
        </label>
        <label>
          <span>Last name</span>
          <input name="last_name" value={form.last_name} onChange={updateField} autoComplete="family-name" />
        </label>
      </div>

      <label>
        <span>Email</span>
        <input type="email" name="email" value={form.email} onChange={updateField} autoComplete="email" required />
      </label>

      <div className="form-grid two">
        <label>
          <span>Phone</span>
          <input name="phone" value={form.phone} onChange={updateField} placeholder="+254700000001" autoComplete="tel" />
        </label>
        <label>
          <span>Country</span>
          <input name="country_code" value={form.country_code} onChange={updateField} maxLength="2" required />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Password</span>
          <input type="password" name="password" value={form.password} onChange={updateField} autoComplete="new-password" required />
        </label>
        <label>
          <span>Confirm password</span>
          <input type="password" name="password_confirm" value={form.password_confirm} onChange={updateField} autoComplete="new-password" required />
        </label>
      </div>

      <label className="auth-check">
        <input type="checkbox" name="receive_order_updates" checked={form.receive_order_updates} onChange={updateField} />
        <span>Send me order updates</span>
      </label>

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        <MaterialIcon name="how_to_reg" size={19} />
        {loading ? "Creating..." : "Create account"}
      </button>

      <p className="auth-switch">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </form>
  );
}
