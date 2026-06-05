import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import EmailVerificationNotice from "../../components/account/EmailVerificationNotice.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { normalizeApiError } from "../../utils/errorHandler";
import "./preferences.css";

const DEFAULT_PREFERENCES = {
  receive_order_updates: true,
  receive_marketing_emails: false,
  two_factor_email_enabled: false,
  email_verified: false,
  email_verified_at: null,
  preferred_currency: "",
  country_code: "",
  phone: "",
  company: ""
};

function buildPreferencePayload(preferences) {
  return {
    receive_order_updates: Boolean(preferences.receive_order_updates),
    receive_marketing_emails: Boolean(preferences.receive_marketing_emails),
    two_factor_email_enabled: Boolean(preferences.two_factor_email_enabled),
    preferred_currency: preferences.preferred_currency || "",
    country_code: preferences.country_code || "",
    phone: preferences.phone || "",
    company: preferences.company || ""
  };
}

export default function PreferencesPage() {
  const { user } = useAuth();
  const notify = useUiStore((state) => state.notify);
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedMessage, setSavedMessage] = useState("");

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
    setSavedMessage("");
    try {
      const payload = await storefrontExtrasApi.account.updatePreferences(buildPreferencePayload(preferences));
      setPreferences({ ...DEFAULT_PREFERENCES, ...(payload?.preferences || preferences) });
      setSavedMessage("Saved. These settings will be used for future account and store emails.");
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
          <h1>Email and store settings</h1>
          <p>Choose optional store emails, sign-in protection, and checkout defaults.</p>
        </div>
      </div>

      {loading ? <Spinner label="Loading preferences" /> : null}
      <Alert tone="warning">{error}</Alert>

      {!loading ? (
        <form className="preferences-form" onSubmit={handleSubmit}>
          <div className="preferences-status-grid" aria-label="Preference summary">
            <article className="preference-status-card">
              <MaterialIcon name={preferences.email_verified ? "mark_email_read" : "mark_email_unread"} size={22} />
              <div>
                <strong>{preferences.email_verified ? "Email verified" : "Verify your email"}</strong>
                <span>{preferences.email_verified ? "Security emails can reach you." : "Required before email sign-in codes."}</span>
              </div>
            </article>
            <article className="preference-status-card">
              <MaterialIcon name="local_shipping" size={22} />
              <div>
                <strong>{preferences.receive_order_updates ? "Order emails on" : "Order emails off"}</strong>
                <span>Confirmations and delivery updates.</span>
              </div>
            </article>
            <article className="preference-status-card">
              <MaterialIcon name="campaign" size={22} />
              <div>
                <strong>{preferences.receive_marketing_emails ? "Offers enabled" : "Offers paused"}</strong>
                <span>Campaign and discovery messages.</span>
              </div>
            </article>
            <article className="preference-status-card">
              <MaterialIcon name="password" size={22} />
              <div>
                <strong>{preferences.two_factor_email_enabled ? "Email code enabled" : "Email code disabled"}</strong>
                <span>Extra sign-in verification.</span>
              </div>
            </article>
          </div>

          <section className="preferences-panel">
            <div className="preferences-panel-header">
              <span className="preferences-panel-icon">
                <MaterialIcon name="outgoing_mail" size={21} />
              </span>
              <div>
                <h2>Email delivery</h2>
                <p>Control optional messages. Security emails remain active to protect your account.</p>
              </div>
            </div>
            <EmailVerificationNotice user={user} compact />
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
            <label className={`preference-toggle${!preferences.email_verified ? " is-disabled" : ""}`}>
              <input
                type="checkbox"
                checked={Boolean(preferences.two_factor_email_enabled)}
                disabled={!preferences.email_verified}
                onChange={(event) => updateField("two_factor_email_enabled", event.target.checked)}
              />
              <span>
                <strong>Email sign-in code</strong>
                <small>
                  Require a one-time code sent by email when signing in. Verify your email before enabling this.
                </small>
              </span>
            </label>
          </section>

          <section className="preferences-info-grid">
            <article className="preferences-info-card">
              <MaterialIcon name="verified_user" size={21} />
              <div>
                <strong>Always sent for safety</strong>
                <p>Email verification, password reset, password changed, reactivation review, and sign-in codes are security messages.</p>
              </div>
            </article>
            <article className="preferences-info-card">
              <MaterialIcon name="notifications_active" size={21} />
              <div>
                <strong>Product alert emails</strong>
                <p>Availability alerts are managed from the product alerts screen, so customers can control each product separately.</p>
                <Link to="/account/product-alerts">Manage product alerts</Link>
              </div>
            </article>
            <article className="preferences-info-card">
              <MaterialIcon name="inbox" size={21} />
              <div>
                <strong>Notifications center</strong>
                <p>Important account activity is also available in your inbox inside the storefront.</p>
                <Link to="/account/notifications">Open notifications</Link>
              </div>
            </article>
          </section>

          <section className="preferences-panel">
            <div className="preferences-panel-header">
              <span className="preferences-panel-icon">
                <MaterialIcon name="storefront" size={21} />
              </span>
              <div>
                <h2>Store defaults</h2>
                <p>These details help prefill checkout, account forms, and regional prices.</p>
              </div>
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

          <div className="preferences-actions">
            <button className="primary-button preferences-submit" type="submit" disabled={saving}>
              <MaterialIcon name="save" size={18} />
              {saving ? "Saving..." : "Save preferences"}
            </button>
            {savedMessage ? <span className="preferences-saved">{savedMessage}</span> : null}
          </div>
        </form>
      ) : null}
    </section>
  );
}
