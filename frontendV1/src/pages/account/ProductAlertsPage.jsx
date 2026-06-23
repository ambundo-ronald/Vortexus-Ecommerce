import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import EmailTouchpointCard from "../../components/account/EmailTouchpointCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { formatDate } from "../../utils/formatDate";
import { normalizeApiError } from "../../utils/errorHandler";
import { productImageUrl } from "../../utils/productImages";
import { productId, productInitials, productPrice, productTitle } from "../../utils/productDisplay";

export default function ProductAlertsPage() {
  const notify = useUiStore((state) => state.notify);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.productAlerts.list();
      setAlerts(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load product alerts.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  async function removeAlert(alert) {
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.productAlerts.remove(alert.id);
      notify({ title: "Alert cancelled", message: "You will no longer receive this stock alert.", icon: "notifications_off" });
      await loadAlerts();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not cancel alert.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="account-section-title">
        <div>
          <p className="eyebrow">Stock alerts</p>
          <h1>Product availability</h1>
        </div>
      </div>

      <EmailTouchpointCard
        actions={[
          { to: "/account/messages", label: "Email history", icon: "inbox" },
          { to: "/account/preferences", label: "Email settings", icon: "tune" }
        ]}
        eyebrow="Stock email alerts"
        icon="notifications_active"
        message="When a product you follow becomes available again, the store sends an email to the address shown on each alert."
        title="Availability emails are tracked here"
        tone="info"
      />

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading product alerts" /> : null}

      {!loading && !alerts.length ? (
        <EmptyState title="No stock alerts" message="Sold-out products you follow will appear here." />
      ) : null}

      {alerts.length ? (
        <div className="alert-list">
          {alerts.map((alert) => (
            <ProductAlertCard key={alert.id} alert={alert} saving={saving} onRemove={removeAlert} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function ProductAlertCard({ alert, saving, onRemove }) {
  const product = alert.product || {};
  const resolvedProductId = productId(product) || alert.product_id;
  const imageUrl = productImageUrl(product);
  const price = productPrice(product);
  const title = productTitle(product, `Product #${alert.product_id}`);
  const status = alert.status || "Pending";
  const statusKey = String(status).toLowerCase().replace(/[^a-z0-9]+/g, "-");
  const dateLabel = alert.date_cancelled
    ? `Cancelled ${formatDate(alert.date_cancelled)}`
    : alert.date_confirmed
      ? `Confirmed ${formatDate(alert.date_confirmed)}`
      : `Created ${formatDate(alert.date_created)}`;

  return (
    <article className="product-alert-card">
      <Link className="product-alert-card__media" to={resolvedProductId ? `/products/${resolvedProductId}` : "/catalog"}>
        {imageUrl ? <img src={imageUrl} alt={title} loading="lazy" /> : <span>{productInitials(title)}</span>}
      </Link>
      <div className="product-alert-card__body">
        <strong>{title}</strong>
        <span>{price.label || "Price on request"}</span>
        <small>{dateLabel}</small>
        <em className={`product-alert-card__status product-alert-card__status--${statusKey}`}>{status}</em>
      </div>
      <div className="product-alert-card__actions">
        <Link className="secondary-button" to={resolvedProductId ? `/products/${resolvedProductId}` : "/catalog"}>
          <MaterialIcon name="open_in_new" size={17} />
          View
        </Link>
        <span className="product-alert-card__email">
          <MaterialIcon name="alternate_email" size={16} />
          {alert.email}
        </span>
        {statusKey !== "cancelled" && statusKey !== "canceled" ? (
          <button className="danger-link" type="button" disabled={saving} onClick={() => void onRemove(alert)}>
            Cancel
          </button>
        ) : null}
      </div>
    </article>
  );
}
