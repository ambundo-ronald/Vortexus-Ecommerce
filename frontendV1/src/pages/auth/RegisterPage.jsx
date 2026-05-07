import { Navigate, useNavigate } from "react-router-dom";

import RegisterForm from "../../components/auth/RegisterForm.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function RegisterPage() {
  const navigate = useNavigate();
  const auth = useAuth();

  async function handleRegister(payload) {
    await auth.register(payload);
    navigate("/account", { replace: true });
  }

  if (auth.user) return <Navigate to="/account" replace />;

  return (
    <section className="auth-page">
      <RegisterForm loading={auth.loading} error={auth.error} onSubmit={handleRegister} />
    </section>
  );
}
