import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { normalizeApiError } from "../../utils/errorHandler";
import "./preferences.css";

const DEFAULT_PREFERENCES = {
  receive_order_updates: true,
  receive_marketing_emails: false,
  preferred_currency: "",
  country_code: "",
  phone: "",
  company: ""
};

export default function PreferencesPage() {
  const notify = useUiStore((state) => state.notify);
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadPreferences = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.account.preferences();
      setPreferences({ ...DEFAULT_PREFERENCES, ...(payload?.preferences || {}) });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load preferences.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  function updateField(field, value) {
    setPreferences((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.account.updatePreferences(preferences);
      setPreferences({ ...DEFAULT_PREFERENCES, ...(payload?.preferences || preferences) });
      notify({ title: "Preferences saved", message: "Your store settings were updated.", icon: "tune" });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not save preferences.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page preferences-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="preferences-hero">
        <div>
          <p className="eyebrow">Preferences</p>
          <h1>Store settings</h1>
          <p>Choose how the store should communicate with you.</p>
        </div>
      </div>

      {loading ? <Spinner label="Loading preferences" /> : null}
      <Alert tone="warning">{error}</Alert>

      {!loading ? (
        <form className="preferences-form" onSubmit={handleSubmit}>
          <section className="preferences-panel">
            <div>
              <h2>Communication</h2>
              <p>Control updates and promotional messages.</p>
            </div>
            <label className="preference-toggle">
              <input
                type="checkbox"
                checked={Boolean(preferences.receive_order_updates)}
                onChange={(event) => updateField("receive_order_updates", event.target.checked)}
              />
              <span>
                <strong>Order updates</strong>
                <small>Receive emails for order confirmations, delivery changes, and status updates.</small>
              </span>
            </label>
            <label className="preference-toggle">
              <input
                type="checkbox"
                checked={Boolean(preferences.receive_marketing_emails)}
                onChange={(event) => updateField("receive_marketing_emails", event.target.checked)}
              />
              <span>
                <strong>Marketing emails</strong>
                <small>Receive offer, campaign, and product discovery emails.</small>
              </span>
            </label>
          </section>

          <section className="preferences-panel">
            <div>
              <h2>Store defaults</h2>
              <p>These details help prefill checkout and account forms.</p>
            </div>
            <div className="preferences-grid">
              <label>
                <span>Preferred currency</span>
                <select
                  value={preferences.preferred_currency || ""}
                  onChange={(event) => updateField("preferred_currency", event.target.value)}
                >
                  <option value="">Use store default</option>
                  <option value="KES">KES</option>
                  <option value="USD">USD</option>
                </select>
              </label>
              <label>
                <span>Country code</span>
                <input
                  type="text"
                  value={preferences.country_code || ""}
                  placeholder="KE"
                  onChange={(event) => updateField("country_code", event.target.value.toUpperCase())}
                />
              </label>
              <label>
                <span>Phone</span>
                <input
                  type="tel"
                  value={preferences.phone || ""}
                  placeholder="+254..."
                  onChange={(event) => updateField("phone", event.target.value)}
                />
              </label>
              <label>
                <span>Company</span>
                <input
                  type="text"
                  value={preferences.company || ""}
                  placeholder="Company name"
                  onChange={(event) => updateField("company", event.target.value)}
                />
              </label>
            </div>
          </section>

          <button className="primary-button preferences-submit" type="submit" disabled={saving}>
            <MaterialIcon name="save" size={18} />
            {saving ? "Saving..." : "Save preferences"}
          </button>
        </form>
      ) : null}
    </section>
  );
}
