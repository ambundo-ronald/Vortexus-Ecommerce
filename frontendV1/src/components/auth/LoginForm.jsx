import { useState } from "react";
import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function LoginForm({ loading = false, error = "", onSubmit }) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
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

      <label>
        <span>Email or username</span>
        <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" required />
      </label>

      <label>
        <span>Password</span>
        <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
      </label>

      <button className="primary-button auth-submit" type="submit" disabled={loading}>
        <MaterialIcon name="login" size={19} />
        {loading ? "Signing in..." : "Sign in"}
      </button>

      <p className="auth-switch">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </form>
  );
}
