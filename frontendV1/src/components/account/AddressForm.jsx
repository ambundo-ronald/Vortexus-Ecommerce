import { useEffect, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const emptyAddress = {
  title: "",
  first_name: "",
  last_name: "",
  line1: "",
  line2: "",
  line3: "",
  line4: "",
  state: "",
  postcode: "",
  country_code: "KE",
  phone_number: "",
  notes: "",
  is_default_for_shipping: false,
  is_default_for_billing: false
};

export default function AddressForm({
  address = null,
  loading = false,
  title = "Address",
  description = "Save address details for faster checkout.",
  submitLabel = "Save address",
  onSubmit,
  onCancel
}) {
  const [form, setForm] = useState(() => ({ ...emptyAddress, ...(address || {}) }));

  useEffect(() => {
    setForm({ ...emptyAddress, ...(address || {}) });
  }, [address]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  }

  function submit(event) {
    event.preventDefault();
    const companyOrSite = form.line1 || form.line3 || form.title || [form.first_name, form.last_name].filter(Boolean).join(" ");

    onSubmit?.({
      ...form,
      line1: companyOrSite || "Delivery point",
      line2: "",
      line3: form.line3 && form.line3 !== companyOrSite ? form.line3 : "",
      line4: "",
      state: "",
      postcode: "",
      country_code: String(form.country_code || "KE").toUpperCase()
    });
  }

  return (
    <form className="auth-card account-form address-form" onSubmit={submit}>
      <div className="auth-card__head">
        <span><MaterialIcon name="location_on" size={24} /></span>
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </div>

      <label>
        <span>Label</span>
        <input name="title" value={form.title} onChange={updateField} placeholder="Site, office, home" />
      </label>

      <div className="form-grid two">
        <label>
          <span>First name</span>
          <input name="first_name" value={form.first_name} onChange={updateField} required autoComplete="given-name" />
        </label>
        <label>
          <span>Last name</span>
          <input name="last_name" value={form.last_name} onChange={updateField} required autoComplete="family-name" />
        </label>
      </div>

      <label>
        <span>Phone number</span>
        <input name="phone_number" value={form.phone_number} onChange={updateField} placeholder="+254700000001" autoComplete="tel" />
      </label>

      <label>
        <span>Company / site</span>
        <input name="line1" value={form.line1} onChange={updateField} required placeholder="Company, site, office, or pickup point" />
      </label>

      <label>
        <span>Delivery note</span>
        <textarea name="notes" value={form.notes} onChange={updateField} rows="3" placeholder="Gate, landmark, receiving instructions" />
      </label>

      <div className="form-grid two">
        <label className="auth-check">
          <input type="checkbox" name="is_default_for_shipping" checked={form.is_default_for_shipping} onChange={updateField} />
          <span>Default delivery</span>
        </label>
        <label className="auth-check">
          <input type="checkbox" name="is_default_for_billing" checked={form.is_default_for_billing} onChange={updateField} />
          <span>Default billing</span>
        </label>
      </div>

      <div className="address-form__actions">
        {onCancel ? (
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
        <button className="primary-button" type="submit" disabled={loading}>
          <MaterialIcon name="save" size={19} />
          {loading ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
