import { Link, useLocation } from "react-router-dom";

import MaterialIcon from "../../components/ui/MaterialIcon.jsx";

export default function UnauthorizedPage() {
  const location = useLocation();
  return (
    <section className="error-page surface-panel">
      <span className="error-page__icon">
        <MaterialIcon name="lock" size={34} />
      </span>
      <h1>Sign in required</h1>
      <p>You need an account session to open this page.</p>
      <div className="error-page__actions">
        <Link className="primary-button" to="/login" state={{ from: location }}>
          <MaterialIcon name="login" size={19} />
          Sign in
        </Link>
        <Link className="secondary-button" to="/catalog">
          <MaterialIcon name="storefront" size={19} />
          Continue shopping
        </Link>
      </div>
    </section>
  );
}
