import { Link } from "react-router-dom";

import MaterialIcon from "../../components/ui/MaterialIcon.jsx";

export default function NotFoundPage() {
  return (
    <section className="error-page surface-panel">
      <span className="error-page__icon">
        <MaterialIcon name="travel_explore" size={34} />
      </span>
      <h1>Page not found</h1>
      <p>The page may have moved, or the link may be incorrect.</p>
      <div className="error-page__actions">
        <Link className="primary-button" to="/catalog">
          <MaterialIcon name="storefront" size={19} />
          Shop products
        </Link>
        <Link className="secondary-button" to="/">
          <MaterialIcon name="home" size={19} />
          Home
        </Link>
      </div>
    </section>
  );
}
