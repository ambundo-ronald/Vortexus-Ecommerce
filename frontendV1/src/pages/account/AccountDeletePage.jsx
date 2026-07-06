import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import PasswordInput from "../../components/ui/PasswordInput.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useUiStore } from "../../store/ui.store";
import { normalizeApiError } from "../../utils/errorHandler";
import "./accountDelete.css";

export default function AccountDeletePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const notify = useUiStore((state) => state.notify);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = password.length > 0 && confirmation.trim().toLowerCase() === "delete";

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.account.delete({ password });
      notify({
        tone: "info",
        title: "Account deactivated",
        message: "Your account has been deactivated.",
        icon: "person_remove"
      });
      await logout();
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not deactivate account.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page account-delete-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="account-delete-hero">
        <span className="account-delete-hero__icon">
          <MaterialIcon name="person_remove" size={28} />
        </span>
        <div>
          <p className="eyebrow">Danger zone</p>
          <h1>Delete account</h1>
          <p>This deactivates your customer account and signs you out.</p>
        </div>
      </div>

      <Alert tone="warning">{error}</Alert>

      <form className="account-delete-panel" onSubmit={handleSubmit}>
        <div className="account-delete-warning">
          <MaterialIcon name="warning" size={24} />
          <div>
            <strong>Before you continue</strong>
            <p>
              This action disables account access. Your existing orders may still be retained by the store for fulfilment,
              audit, tax, and support records.
            </p>
          </div>
        </div>

        <label>
          <span>Password</span>
          <PasswordInput
            value={password}
            autoComplete="current-password"
            placeholder="Enter your password"
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <label>
          <span>Type DELETE to confirm</span>
          <input
            type="text"
            value={confirmation}
            placeholder="DELETE"
            onChange={(event) => setConfirmation(event.target.value)}
          />
        </label>

        <div className="account-delete-actions">
          <Link className="secondary-button" to="/account">
            Cancel
          </Link>
          <button className="account-delete-button" type="submit" disabled={saving || !canSubmit}>
            <MaterialIcon name="person_remove" size={18} />
            {saving ? "Deactivating..." : "Deactivate account"}
          </button>
        </div>
      </form>
    </section>
  );
}
