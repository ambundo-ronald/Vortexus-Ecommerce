import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { supplierApi } from "../../api/supplier.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useUiStore } from "../../store/ui.store";

const initialForm = {
  company_name: "",
  contact_name: "",
  phone: "",
  country_code: "KE",
  website: "",
  notes: ""
};

export default function SupplierApplyPage() {
  const navigate = useNavigate();
  const notify = useUiStore((state) => state.notify);
  const { user, initialized, loadUser } = useAuth();
  const [profilePayload, setProfilePayload] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!initialized || !user) return;
      setLoading(true);
      setError("");
      try {
        const payload = await supplierApi.profile();
        if (!mounted) return;
        setProfilePayload(payload);
        const supplier = payload?.supplier;
        if (supplier) {
          setForm({
            company_name: supplier.company_name || "",
            contact_name: supplier.contact_name || "",
            phone: supplier.phone || "",
            country_code: supplier.country_code || "KE",
            website: supplier.website || "",
            notes: supplier.notes || ""
          });
        }
      } catch (err) {
        if (mounted) setError(err.normalized?.message || err.message || "Could not load supplier application.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, [initialized, user]);

  if (!initialized) return <Spinner label="Checking account" />;
  if (!user) return <Navigate to="/login" replace />;
  if (profilePayload?.supplier) return <Navigate to="/supplier" replace />;
  if (loading) return <Spinner label="Loading supplier application" />;

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submitApplication(event) {
    event.preventDefault();
    setError("");
    if (!form.company_name.trim()) {
      setError("Company name is required.");
      return;
    }

    setSaving(true);
    try {
      await supplierApi.createProfile({
        company_name: form.company_name.trim(),
        contact_name: form.contact_name.trim(),
        phone: form.phone.trim(),
        country_code: form.country_code.trim().toUpperCase(),
        website: form.website.trim(),
        notes: form.notes.trim()
      });
      await loadUser({ silent: true });
      notify({ title: "Application submitted", message: "Your supplier profile is pending review.", icon: "store" });
      navigate("/supplier", { replace: true });
    } catch (err) {
      setError(err.normalized?.message || err.message || "Could not submit supplier application.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="auth-page supplier-apply-page">
      <form className="auth-card supplier-apply-card" onSubmit={submitApplication}>
        <div className="auth-card__head">
          <span><MaterialIcon name="store" size={24} /></span>
          <div>
            <h1>Become a supplier</h1>
            <p>Submit your company details for review before selling on Reesolmart.</p>
          </div>
        </div>

        <Alert>{error}</Alert>

        <label>
          <span>Company name</span>
          <input value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} required />
        </label>
        <label>
          <span>Contact name</span>
          <input value={form.contact_name} onChange={(event) => updateField("contact_name", event.target.value)} />
        </label>
        <label>
          <span>Phone</span>
          <input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
        </label>
        <label>
          <span>Country code</span>
          <input value={form.country_code} maxLength={2} onChange={(event) => updateField("country_code", event.target.value)} />
        </label>
        <label>
          <span>Website</span>
          <input type="url" value={form.website} onChange={(event) => updateField("website", event.target.value)} />
        </label>
        <label>
          <span>Business description</span>
          <textarea rows={5} value={form.notes} onChange={(event) => updateField("notes", event.target.value)} />
        </label>

        <button className="primary-button auth-submit" type="submit" disabled={saving}>
          <MaterialIcon name={saving ? "hourglass_top" : "send"} size={19} />
          {saving ? "Submitting..." : "Submit application"}
        </button>
      </form>
    </section>
  );
}
