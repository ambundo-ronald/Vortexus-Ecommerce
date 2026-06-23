import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const { user, verifyEmail, resendEmailVerification, loading, error } = useAuth({ auto: false });
  const [status, setStatus] = useState("pending");
  const [resendMessage, setResendMessage] = useState("");
  const [resendError, setResendError] = useState("");

  useEffect(() => {
    const uid = searchParams.get("uid") || "";
    const token = searchParams.get("token") || searchParams.get("amp;token") || "";

    if (!uid || !token) {
      setStatus("invalid");
      return;
    }

    let active = true;
    setStatus("pending");
    verifyEmail({ uid, token })
      .then(() => {
        if (active) setStatus("verified");
      })
      .catch(() => {
        if (active) setStatus("failed");
      });

    return () => {
      active = false;
    };
  }, [searchParams, verifyEmail]);

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-card__header">
          <span><MaterialIcon name="mark_email_read" size={24} /></span>
          <div>
            <p className="eyebrow">Account security</p>
            <h1>Email verification</h1>
          </div>
        </div>

        {status === "pending" || loading ? <Spinner label="Verifying email" /> : null}
        {status === "invalid" ? <Alert>Verification link is missing required details.</Alert> : null}
        {status === "failed" ? <Alert>{error || "Verification link is invalid, expired, or already used. Links expire in 30 minutes."}</Alert> : null}
        {status === "verified" ? (
          <Alert tone="success">
            Your email address has been verified. {user ? "Your account is now updated." : "You can now sign in."}
          </Alert>
        ) : null}

        {user && status !== "verified" ? (
          <div className="auth-inline-panel">
            <div>
              <strong>Need a new link?</strong>
              <span>Send another verification email to your current account address.</span>
            </div>
            <button
              className="secondary-button"
              type="button"
              disabled={loading}
              onClick={async () => {
                setResendMessage("");
                setResendError("");
                try {
                  const response = await resendEmailVerification();
                  setResendMessage(response?.detail || "Verification email sent.");
                } catch (requestError) {
                  setResendError(requestError?.normalized?.message || "Could not send verification email.");
                }
              }}
            >
              <MaterialIcon name="send" size={17} />
              Resend email
            </button>
          </div>
        ) : null}

        <Alert tone="success">{resendMessage}</Alert>
        <Alert tone="warning">{resendError}</Alert>

        <Link className="primary-button" to={user ? "/account" : "/login"}>
          {user ? "Go to account" : "Sign in"}
        </Link>
      </div>
    </section>
  );
}
