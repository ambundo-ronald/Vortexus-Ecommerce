import { Link } from "react-router-dom";
import { useState } from "react";

import { useAuth } from "../../hooks/useAuth";
import { normalizeApiError } from "../../utils/errorHandler";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import "./EmailVerificationNotice.css";

export function isEmailVerified(user) {
  return Boolean(user?.email_verification?.is_verified || user?.email_verified);
}

export default function EmailVerificationNotice({ user, compact = false, showVerified = false }) {
  const { resendEmailVerification } = useAuth({ auto: false });
  const verified = isEmailVerified(user);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  if (!user) return null;

  async function handleResend() {
    setSending(true);
    setMessage("");
    setError("");
    try {
      const response = await resendEmailVerification();
      setMessage(response?.detail || "Verification email sent. Check your inbox.");
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not send verification email.").message);
    } finally {
      setSending(false);
    }
  }

  if (verified) {
    if (!showVerified) return null;
    return (
      <div className={`email-verification-status${compact ? " email-verification-status--compact" : ""}`}>
        <span className="email-verification-status__icon">
          <MaterialIcon name="mark_email_read" size={18} />
        </span>
        <div>
          <strong>Email verified</strong>
          <small>Your account can receive security and order emails.</small>
        </div>
      </div>
    );
  }

  return (
    <div className={`email-verification-notice${compact ? " email-verification-notice--compact" : ""}`}>
      <span className="email-verification-notice__icon">
        <MaterialIcon name="outgoing_mail" size={22} />
      </span>
      <div className="email-verification-notice__body">
        <strong>Verify your email address</strong>
        <p>
          We sent a verification link to <span>{user.email}</span>. Confirm it so security, order, quote, and stock
          alert emails reach the right inbox. The link expires in 30 minutes.
        </p>
        {message ? <small className="email-verification-notice__success">{message}</small> : null}
        {error ? <small className="email-verification-notice__error">{error}</small> : null}
      </div>
      <div className="email-verification-notice__actions">
        <button className="secondary-button" type="button" disabled={sending} onClick={handleResend}>
          <MaterialIcon name="send" size={17} />
          {sending ? "Sending..." : "Resend email"}
        </button>
        <Link className="text-action" to="/account/profile">
          Check address
        </Link>
      </div>
    </div>
  );
}
