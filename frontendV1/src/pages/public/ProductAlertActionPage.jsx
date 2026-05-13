import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";

export default function ProductAlertActionPage({ action = "confirm" }) {
  const { key } = useParams();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const isCancel = action === "cancel";

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const request = isCancel
      ? storefrontExtrasApi.productAlerts.cancel(key)
      : storefrontExtrasApi.productAlerts.confirm(key);
    request
      .then((payload) => {
        if (!active) return;
        setAlert(payload?.alert || null);
      })
      .catch((requestError) => {
        if (!active) return;
        setError(normalizeApiError(requestError, "Could not update this product alert.").message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isCancel, key]);

  return (
    <section className="auth-page">
      <div className="auth-card product-alert-result">
        <div className="auth-card__head">
          <span><MaterialIcon name={isCancel ? "notifications_off" : "notifications_active"} size={24} /></span>
          <div>
            <h1>{isCancel ? "Alert cancelled" : "Alert confirmed"}</h1>
            <p>{isCancel ? "You will not receive this stock alert." : "We will notify you when this product is available."}</p>
          </div>
        </div>

        {loading ? <Spinner label="Updating alert" /> : null}
        <Alert>{error}</Alert>
        {alert ? (
          <div className="auth-inline-panel">
            <strong>Product #{alert.product_id}</strong>
            <span>{alert.email} · {alert.status}</span>
            <Link className="secondary-button" to={`/products/${alert.product_id}`}>
              <MaterialIcon name="inventory_2" size={18} />
              View product
            </Link>
          </div>
        ) : null}
        <Link className="primary-button auth-submit" to="/catalog">
          <MaterialIcon name="storefront" size={18} />
          Continue shopping
        </Link>
      </div>
    </section>
  );
}
