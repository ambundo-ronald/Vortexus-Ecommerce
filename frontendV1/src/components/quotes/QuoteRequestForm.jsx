import { useEffect, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { productId, productTitle } from "../../utils/productDisplay";

const emptyForm = {
  name: "",
  email: "",
  phone: "",
  company: "",
  message: ""
};

export default function QuoteRequestForm({ product, user, loading = false, onSubmit }) {
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      name: current.name || [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.full_name || "",
      email: current.email || user?.email || "",
      phone: current.phone || user?.phone || ""
    }));
  }, [user]);

  useEffect(() => {
    const title = productTitle(product || {}, "");
    if (!title) return;
    setForm((current) => {
      if (current.message) return current;
      return {
        ...current,
        message: `Please send me a quote for ${title}.`
      };
    });
  }, [product]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSubmit?.({
      ...form,
      product_id: productId(product || {})
    });
  }

  return (
    <form className="quote-form checkout-card" onSubmit={submit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name="request_quote" size={20} /></span>
        <div>
          <h2>Request a quote</h2>
        </div>
      </div>

      <label>
        <span>Name</span>
        <input name="name" value={form.name} onChange={updateField} required autoComplete="name" />
      </label>

      <div className="form-grid two">
        <label>
          <span>Email</span>
          <input type="email" name="email" value={form.email} onChange={updateField} autoComplete="email" />
        </label>
        <label>
          <span>Phone</span>
          <input name="phone" value={form.phone} onChange={updateField} autoComplete="tel" placeholder="+254700000001" />
        </label>
      </div>

      <label>
        <span>Company or site</span>
        <input name="company" value={form.company} onChange={updateField} autoComplete="organization" />
      </label>

      <label>
        <span>Message</span>
        <textarea name="message" value={form.message} onChange={updateField} required rows="5" />
      </label>

      <button className="primary-button checkout-submit" type="submit" disabled={loading}>
        <MaterialIcon name="send" size={19} />
        {loading ? "Sending..." : "Send request"}
      </button>
    </form>
  );
}
