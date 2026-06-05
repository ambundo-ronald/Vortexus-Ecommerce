import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import "./LoginForm.css";

export default function LoginForm({
  loading = false,
  error = "",
  errorCode = "",
  pendingTwoFactor = null,
  onSubmit,
  onRequestReactivation,
  onVerifyTwoFactor,
  onCancelTwoFactor
}) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [reactivationMessage, setReactivationMessage] = useState("");
  const [reactivationError, setReactivationError] = useState("");
  const [now, setNow] = useState(() => Date.now());

  const accountInactive = errorCode === "account_inactive";
  const twoFactorExpiresAt = useMemo(() => {
    if (!pendingTwoFactor) return 0;
    if (pendingTwoFactor.expires_at) {
      const parsed = Date.parse(pendingTwoFactor.expires_at);
      if (Number.isFinite(parsed)) return parsed;
    }
    const fallbackSeconds = Number(pendingTwoFactor.expires_in_seconds || 600);
    return Date.now() + fallbackSeconds * 1000;
  }, [pendingTwoFactor]);
  const remainingSeconds = pendingTwoFactor ? Math.max(0, Math.ceil((twoFactorExpiresAt - now) / 1000)) : 0;
  const remainingLabel = `${Math.floor(remainingSeconds / 60)}:${String(remainingSeconds % 60).padStart(2, "0")}`;
  const canVerifyTwoFactor = !pendingTwoFactor || code.length === 6;

  useEffect(() => {
    if (!pendingTwoFactor) return undefined;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [pendingTwoFactor]);

  function handleSubmit(event) {
    event.preventDefault();
    if (pendingTwoFactor) {
      if (!canVerifyTwoFactor) return;
      onVerifyTwoFactor?.({ challenge_id: pendingTwoFactor.challenge_id, code });
      return;
    }
    onSubmit?.({ identifier, password });
  }

  function handleCancelTwoFactor() {
    setCode("");
    onCancelTwoFactor?.();
  }

  async function handleReactivationRequest() {
    if (!identifier.trim()) return;
    setReactivationMessage("");
    setReactivationError("");
    try {
      const response = await onRequestReactivation?.({ identifier: identifier.trim() });
      setReactivationMessage(response?.detail || "Support will review the account reactivation request.");
    } catch (requestError) {
      setReactivationError(requestError?.normalized?.message || "Could not request account reactivation.");
    }
  }

  return (
    <form className="auth-card" onSubmit={handleSubmit}>
      <div className="auth-card__head">
        <span><MaterialIcon name="person" size={24} /></span>
        <div>
          <h1>Sign in</h1>
          <p>Access your orders and saved account details.</p>
        </div>
      </div>

      <Alert tone={accountInactive ? "warning" : "danger"}>{error}</Alert>

      {accountInactive ? (
        <div className="auth-inline-panel">
          <div>
            <strong>Account deactivated</strong>
            <span>
              This account was deactivated after deletion. Request reactivation, then sign in once support restores it.
            </span>
          </div>
          <button className="secondary-button" type="button" disabled={loading || !identifier.trim()} onClick={handleReactivationRequest}>
            <MaterialIcon name="support_agent" size={17} />
            Request reactivation
          </button>
        </div>
      ) : null}

      <Alert tone="info">{reactivationMessage}</Alert>
      <Alert tone="warning">{reactivationError}</Alert>

      {pendingTwoFactor ? (
        <div className="auth-two-factor">
          <span className="auth-two-factor__icon">
            <MaterialIcon name="mark_email_unread" size={24} />
          </span>
          <div>
            <strong>Check your email</strong>
            <span>
              {remainingSeconds > 0
                ? `Enter the 6-digit code sent to ${pendingTwoFactor.email_mask || "your email"}. It expires in ${remainingLabel}.`
                : "This code has expired. Use another account and sign in again to send a new code."}
            </span>
          </div>
        </div>
      ) : null}

      {!pendingTwoFactor ? (
        <>
          <label>
            <span>Email or username</span>
            <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" required />
          </label>

          <label>
            <span className="auth-label-row">
              Password
              <Link to="/forgot-password">Forgot?</Link>
            </span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
          </label>
        </>
      ) : (
        <label className="auth-code-field">
          <span>Verification code</span>
          <input
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            autoComplete="one-time-code"
            inputMode="numeric"
            maxLength={6}
            placeholder="000000"
            required
            autoFocus
          />
          <span className="auth-code-field__note">
            {pendingTwoFactor?.max_attempts ? `${pendingTwoFactor.max_attempts} attempts allowed. ` : ""}
            Did not get it? Use another account and sign in again to send a new code.
          </span>
        </label>
      )}

      <button
        className="primary-button auth-submit"
        type="submit"
        disabled={loading || Boolean(pendingTwoFactor && (!canVerifyTwoFactor || remainingSeconds <= 0))}
      >
        <MaterialIcon name={pendingTwoFactor ? "verified_user" : "login"} size={19} />
        {loading ? "Checking..." : pendingTwoFactor ? "Verify code" : "Sign in"}
      </button>

      {pendingTwoFactor ? (
        <button className="secondary-button auth-submit" type="button" disabled={loading} onClick={handleCancelTwoFactor}>
          Use another account
        </button>
      ) : null}

      <p className="auth-switch">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </form>
  );
}
