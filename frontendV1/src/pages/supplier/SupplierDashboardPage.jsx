import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { supplierApi } from "../../api/supplier.api";
import SupplierDashboardKPI from "../../components/supplier/SupplierDashboardKPI.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";

export default function SupplierDashboardPage() {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await supplierApi.dashboard();
        if (mounted) setPayload(data);
      } catch (err) {
        if (mounted) setError(err.normalized?.message || err.message || "Could not load supplier dashboard.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <Spinner label="Loading supplier dashboard" />;

  const supplier = payload?.supplier;
  const metrics = payload?.metrics || {};
  const approved = supplier?.status === "approved";

  return (
    <section className="account-page supplier-page">
      <div className="account-hero surface-panel">
        <span className="account-avatar">{initials(supplier?.company_name || "Supplier")}</span>
        <div>
          <p className="eyebrow">Supplier Portal</p>
          <h1>{supplier?.company_name || "Supplier account"}</h1>
          <p>{supplier?.partner?.name || "Partner profile"}</p>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {!approved ? (
        <div className="surface-panel supplier-status-panel">
          <MaterialIcon name={supplier?.status === "suspended" ? "block" : "pending_actions"} size={28} />
          <div>
            <h2>{supplier?.status === "suspended" ? "Supplier access suspended" : "Application under review"}</h2>
            <p>Your supplier account is {formatStatus(supplier?.status)}. Product uploads and fulfillment actions are available after approval.</p>
            {supplier?.status_note ? <p className="supplier-status-panel__note">{supplier.status_note}</p> : null}
            {supplier?.account_manager ? <p>Account manager: {supplier.account_manager.name || supplier.account_manager.email}</p> : null}
          </div>
        </div>
      ) : null}

      <div className="supplier-kpi-grid">
        <SupplierDashboardKPI icon="inventory_2" label="Products" value={metrics.product_count} hint="All supplier offers" />
        <SupplierDashboardKPI icon="visibility" label="Live products" value={metrics.public_product_count} hint="Visible on storefront" />
        <SupplierDashboardKPI icon="rate_review" label="Pending review" value={metrics.pending_product_count} hint="Awaiting staff approval" />
        <SupplierDashboardKPI icon="warehouse" label="Inventory units" value={metrics.inventory_units} hint="Across stock records" />
      </div>

      {approved ? (
        <div className="account-action-grid">
          <Link className="account-action-card" to="/supplier/products">
            <MaterialIcon name="inventory_2" size={24} />
            <strong>Products</strong>
            <span>Upload products and track approval</span>
          </Link>
          <Link className="account-action-card" to="/supplier/orders">
            <MaterialIcon name="local_shipping" size={24} />
            <strong>Orders</strong>
            <span>Fulfill assigned order lines</span>
          </Link>
        </div>
      ) : null}
    </section>
  );
}

function initials(value = "") {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  return (parts[0]?.[0] || "S") + (parts[1]?.[0] || "");
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()) || "Pending";
}
