import { useState } from "react";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import PasswordInput from "../ui/PasswordInput.jsx";

const emptyForm = {
  current_password: "",
  new_password: "",
  new_password_confirm: ""
};

export default function ChangePasswordForm({ loading = false, error = "", onSubmit }) {
  const [form, setForm] = useState(emptyForm);
  const [success, setSuccess] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSuccess("");
    await onSubmit?.(form);
    setForm(emptyForm);
    setSuccess("Password updated.");
  }

  return (
    <form className="auth-card account-form" onSubmit={submit}>
      <div className="auth-card__head">
        <span><MaterialIcon name="lock_reset" size={24} /></span>
        <div>
          <h1>Password</h1>
          <p>Update your account password.</p>
        </div>
      </div>

      <Alert tone="success">{success}</Alert>
      <Alert>{error}</Alert>

      <label>
        <span>Current password</span>
        <PasswordInput name="current_password" value={form.current_password} onChange={updateField} autoComplete="current-password" required />
      </label>

      <div className="form-grid two">
        <label>
          <span>New password</span>
          <PasswordInput name="new_password" value={form.new_password} onChange={updateField} autoComplete="new-password" required />
        </label>
        <label>
          <span>Confirm new password</span>
          <PasswordInput name="new_password_confirm" value={form.new_password_confirm} onChange={updateField} autoComplete="new-password" required />
        </label>
      </div>

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        <MaterialIcon name="password" size={19} />
        {loading ? "Updating..." : "Change password"}
      </button>
    </form>
  );
}
