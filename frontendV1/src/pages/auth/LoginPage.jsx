import { Navigate, useLocation, useNavigate } from "react-router-dom";

import LoginForm from "../../components/auth/LoginForm.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const from = location.state?.from;
  const next = from ? `${from.pathname || "/account"}${from.search || ""}` : "/account";

  async function handleLogin(payload) {
    const response = await auth.login(payload);
    if (response?.requires_2fa) return;
    navigate(next, { replace: true });
  }

  async function handleTwoFactor(payload) {
    await auth.verifyLoginTwoFactor(payload);
    navigate(next, { replace: true });
  }

  if (auth.user) return <Navigate to={next} replace />;

  return (
    <section className="auth-page">
      <LoginForm
        loading={auth.loading}
        error={auth.error}
        errorCode={auth.errorCode}
        pendingTwoFactor={auth.pendingTwoFactor}
        onSubmit={handleLogin}
        onRequestReactivation={auth.requestReactivation}
        onVerifyTwoFactor={handleTwoFactor}
        onCancelTwoFactor={auth.clearPendingTwoFactor}
      />
    </section>
  );
}
