import { useState } from "react";
import { Link } from "react-router-dom";

import { authApi } from "../../api/auth.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { normalizeApiError } from "../../utils/errorHandler";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [reactivationLoading, setReactivationLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [accountInactive, setAccountInactive] = useState(false);
  const [reactivationMessage, setReactivationMessage] = useState("");
  const [reactivationError, setReactivationError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    setAccountInactive(false);
    setReactivationMessage("");
    setReactivationError("");
    try {
      const payload = await authApi.requestPasswordReset({ email });
      if (payload?.account_inactive) {
        setAccountInactive(true);
      }
      setMessage(payload?.detail || "If that email exists, password reset instructions will be sent.");
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not request a password reset.").message);
    } finally {
      setLoading(false);
    }
  }

  async function requestReactivation() {
    if (!email.trim()) return;
    setReactivationLoading(true);
    setReactivationMessage("");
    setReactivationError("");
    try {
      const payload = await authApi.requestReactivation({ identifier: email.trim() });
      setReactivationMessage(payload?.detail || "Support will review the account reactivation request.");
    } catch (requestError) {
      setReactivationError(normalizeApiError(requestError, "Could not request account reactivation.").message);
    } finally {
      setReactivationLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-card__head">
          <span><MaterialIcon name="lock_reset" size={24} /></span>
          <div>
            <h1>Reset password</h1>
            <p>Enter your account email and we will send a reset link that expires in 30 minutes.</p>
          </div>
        </div>

        <Alert tone={accountInactive ? "warning" : "success"}>{message}</Alert>
        <Alert>{error}</Alert>

        {accountInactive ? (
          <div className="auth-inline-panel">
            <div>
              <strong>Account deactivated</strong>
              <span>Request reactivation first. Support can restore the account before password reset works.</span>
            </div>
            <button className="secondary-button" type="button" disabled={reactivationLoading || !email.trim()} onClick={requestReactivation}>
              <MaterialIcon name="support_agent" size={17} />
              {reactivationLoading ? "Sending..." : "Request reactivation"}
            </button>
          </div>
        ) : null}

        <Alert tone="info">{reactivationMessage}</Alert>
        <Alert tone="warning">{reactivationError}</Alert>

        <label>
          <span>Email address</span>
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
        </label>

        <button className="primary-button auth-submit" type="submit" disabled={loading}>
          <MaterialIcon name="mail" size={19} />
          {loading ? "Sending..." : "Send reset link"}
        </button>

        <p className="auth-switch">
          Remembered it? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </section>
  );
}
