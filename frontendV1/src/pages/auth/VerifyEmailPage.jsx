import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const { verifyEmail, loading, error } = useAuth({ auto: false });
  const [status, setStatus] = useState("pending");

  useEffect(() => {
    const uid = searchParams.get("uid") || "";
    const token = searchParams.get("token") || "";

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
        {status === "failed" ? <Alert>{error || "Verification link is invalid or expired."}</Alert> : null}
        {status === "verified" ? <Alert tone="success">Your email address has been verified.</Alert> : null}

        <Link className="primary-button" to="/account">
          Go to account
        </Link>
      </div>
    </section>
  );
}
