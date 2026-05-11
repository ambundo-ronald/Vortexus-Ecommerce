import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { authApi } from "../../api/auth.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { normalizeApiError } from "../../utils/errorHandler";

const emptyForm = {
  new_password: "",
  new_password_confirm: ""
};

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";
  const hasResetCredentials = Boolean(uid && token);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const passwordMismatch = useMemo(
    () => form.new_password_confirm && form.new_password !== form.new_password_confirm,
    [form.new_password, form.new_password_confirm]
  );

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (!hasResetCredentials) {
      setError("This reset link is missing the required details. Request a new link.");
      return;
    }
    if (passwordMismatch) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const payload = await authApi.confirmPasswordReset({
        uid,
        token,
        new_password: form.new_password,
        new_password_confirm: form.new_password_confirm
      });
      setSuccess(payload?.detail || "Password reset successfully.");
      setForm(emptyForm);
      window.setTimeout(() => navigate("/login", { replace: true }), 1200);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not reset password.").message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-card__head">
          <span><MaterialIcon name="password" size={24} /></span>
          <div>
            <h1>Set new password</h1>
            <p>Choose a new password for your account.</p>
          </div>
        </div>

        {!hasResetCredentials ? (
          <Alert tone="warning">This reset link is incomplete. Request a new password reset link.</Alert>
        ) : null}
        <Alert tone="success">{success}</Alert>
        <Alert>{error}</Alert>

        <label>
          <span>New password</span>
          <input type="password" name="new_password" value={form.new_password} onChange={updateField} autoComplete="new-password" required />
        </label>

        <label>
          <span>Confirm new password</span>
          <input type="password" name="new_password_confirm" value={form.new_password_confirm} onChange={updateField} autoComplete="new-password" required />
        </label>

        {passwordMismatch ? <p className="auth-field-note">Passwords do not match yet.</p> : null}

        <button className="primary-button auth-submit" type="submit" disabled={loading || !hasResetCredentials}>
          <MaterialIcon name="check_circle" size={19} />
          {loading ? "Saving..." : "Save new password"}
        </button>

        <p className="auth-switch">
          Need another link? <Link to="/forgot-password">Request reset</Link>
        </p>
      </form>
    </section>
  );
}
