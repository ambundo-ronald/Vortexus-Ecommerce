import { Link } from "react-router-dom";

import Seo from "../../components/seo/Seo.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";

const notFoundImage = "/404 images/page not found 404.png";

export default function NotFoundPage() {
  return (
    <>
      <Seo
        title="Page not found | Reesolmart"
        description="This Reesolmart page could not be found."
        canonicalPath="/404"
        robots="noindex, nofollow"
      />
      <section className="error-page">
        <img className="error-page__image" src={notFoundImage} alt="Page not found" />
        <p>The page may have moved, or the link may be incorrect.</p>
        <div className="error-page__actions">
          <Link className="primary-button" to="/">
            <MaterialIcon name="home" size={19} />
            Go home
          </Link>
          <Link className="secondary-button" to="/catalog">
            <MaterialIcon name="storefront" size={19} />
            Shop
          </Link>
        </div>
      </section>
    </>
  );
}
