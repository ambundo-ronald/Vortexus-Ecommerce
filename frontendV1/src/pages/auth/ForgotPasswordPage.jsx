import { useState } from "react";
import { Link } from "react-router-dom";

import { authApi } from "../../api/auth.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { normalizeApiError } from "../../utils/errorHandler";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [resetLink, setResetLink] = useState("");

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    setResetLink("");
    try {
      const payload = await authApi.requestPasswordReset({ email });
      setMessage(payload?.detail || "If that email exists, password reset instructions will be sent.");
      if (payload?.uid && payload?.token) {
        const url = new URL("/reset-password", window.location.origin);
        url.searchParams.set("uid", payload.uid);
        url.searchParams.set("token", payload.token);
        setResetLink(url.pathname + url.search);
      }
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not request a password reset.").message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-card__head">
          <span><MaterialIcon name="lock_reset" size={24} /></span>
          <div>
            <h1>Reset password</h1>
            <p>Enter your account email and we will prepare a reset link.</p>
          </div>
        </div>

        <Alert tone="success">{message}</Alert>
        <Alert>{error}</Alert>

        <label>
          <span>Email address</span>
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
        </label>

        <button className="primary-button auth-submit" type="submit" disabled={loading}>
          <MaterialIcon name="mail" size={19} />
          {loading ? "Sending..." : "Send reset link"}
        </button>

        {resetLink ? (
          <div className="auth-inline-panel">
            <strong>Reset link ready</strong>
            <span>Use this link to set a new password.</span>
            <Link className="secondary-button" to={resetLink}>
              <MaterialIcon name="arrow_forward" size={18} />
              Open reset page
            </Link>
          </div>
        ) : null}

        <p className="auth-switch">
          Remembered it? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </section>
  );
}
