import { Link } from "react-router-dom";

import AccountProfileForm from "../../components/account/AccountProfileForm.jsx";
import ChangePasswordForm from "../../components/auth/ChangePasswordForm.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function ProfilePage() {
  const auth = useAuth();

  async function handleProfileUpdate(payload) {
    return auth.updateProfile(payload);
  }

  async function handlePasswordChange(payload) {
    return auth.changePassword(payload);
  }

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>
      <Alert tone="warning">Profile changes save directly to your account.</Alert>
      <AccountProfileForm user={auth.user} loading={auth.loading} error={auth.error} onSubmit={handleProfileUpdate} />
      <ChangePasswordForm loading={auth.loading} error={auth.error} onSubmit={handlePasswordChange} />
    </section>
  );
}
