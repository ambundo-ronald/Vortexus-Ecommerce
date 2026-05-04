import { Navigate, useLocation, useNavigate } from "react-router-dom";

import LoginForm from "../../components/auth/LoginForm.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const next = location.state?.from?.pathname || "/account";

  async function handleLogin(payload) {
    await auth.login(payload);
    navigate(next, { replace: true });
  }

  if (auth.user) return <Navigate to={next} replace />;

  return (
    <section className="auth-page">
      <LoginForm loading={auth.loading} error={auth.error} onSubmit={handleLogin} />
    </section>
  );
}
