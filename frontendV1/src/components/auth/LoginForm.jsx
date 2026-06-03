import { useState } from "react";
import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function LoginForm({ loading = false, error = "", pendingTwoFactor = null, onSubmit, onVerifyTwoFactor, onCancelTwoFactor }) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    if (pendingTwoFactor) {
      onVerifyTwoFactor?.({ challenge_id: pendingTwoFactor.challenge_id, code });
      return;
    }
    onSubmit?.({ identifier, password });
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

      <Alert>{error}</Alert>

      {pendingTwoFactor ? (
        <Alert tone="info">{pendingTwoFactor.detail || "Enter the verification code sent to your email."}</Alert>
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
        <label>
          <span>Verification code</span>
          <input value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} autoComplete="one-time-code" inputMode="numeric" required />
        </label>
      )}

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        <MaterialIcon name={pendingTwoFactor ? "verified_user" : "login"} size={19} />
        {loading ? "Checking..." : pendingTwoFactor ? "Verify code" : "Sign in"}
      </button>

      {pendingTwoFactor ? (
        <button className="secondary-button auth-submit" type="button" disabled={loading} onClick={onCancelTwoFactor}>
          Use another account
        </button>
      ) : null}

      <p className="auth-switch">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </form>
  );
}
