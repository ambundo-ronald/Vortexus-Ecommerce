import { useMemo, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const defaultAddress = {
  first_name: "",
  last_name: "",
  line1: "",
  line2: "",
  line3: "",
  line4: "Nairobi",
  state: "Nairobi",
  postcode: "00100",
  country_code: "KE",
  phone_number: "",
  notes: ""
};

export default function ShippingAddressForm({ address, countries = [], saving = false, onSubmit }) {
  const [form, setForm] = useState(() => ({ ...defaultAddress, ...(address || {}) }));

  const countryOptions = useMemo(() => {
    if (!countries.length) return [{ code: "KE", name: "Kenya" }];
    return countries.map((country) => ({
      code: country.code || country.iso_3166_1_a2 || country.iso_code,
      name: country.name || country.printable_name || country.code
    }));
  }, [countries]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({
      ...form,
      country_code: String(form.country_code || "KE").toUpperCase()
    });
  }

  return (
    <form className="checkout-card shipping-form" onSubmit={handleSubmit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name="location_on" size={20} /></span>
        <div>
          <h2>Delivery details</h2>
          <p>Where should we send your order?</p>
        </div>
      </div>

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
        <input name="phone_number" value={form.phone_number} onChange={updateField} required placeholder="+254700000001" autoComplete="tel" />
      </label>

      <label>
        <span>Address</span>
        <input name="line1" value={form.line1} onChange={updateField} required placeholder="Street, building, road" autoComplete="address-line1" />
      </label>

      <div className="form-grid two">
        <label>
          <span>Apartment or floor</span>
          <input name="line2" value={form.line2} onChange={updateField} autoComplete="address-line2" />
        </label>
        <label>
          <span>Company / site</span>
          <input name="line3" value={form.line3} onChange={updateField} />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Town / city</span>
          <input name="line4" value={form.line4} onChange={updateField} required autoComplete="address-level2" />
        </label>
        <label>
          <span>County / state</span>
          <input name="state" value={form.state} onChange={updateField} autoComplete="address-level1" />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Country</span>
          <select name="country_code" value={form.country_code} onChange={updateField} required>
            {countryOptions.map((country) => (
              <option key={country.code} value={country.code}>{country.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Postcode</span>
          <input name="postcode" value={form.postcode} onChange={updateField} autoComplete="postal-code" />
        </label>
      </div>

      <label>
        <span>Delivery note</span>
        <textarea name="notes" value={form.notes} onChange={updateField} rows="3" placeholder="Gate, landmark, receiving instructions" />
      </label>

      <button className="primary-button checkout-submit" type="submit" disabled={saving}>
        <MaterialIcon name="check" size={19} />
        {saving ? "Saving..." : "Save delivery details"}
      </button>
    </form>
  );
}
