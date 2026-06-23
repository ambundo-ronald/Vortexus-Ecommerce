import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { supplierApi } from "../../api/supplier.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";

export default function SupplierOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const payload = await supplierApi.orders({ page_size: 50 });
        if (mounted) setOrders(payload.results || []);
      } catch (err) {
        if (mounted) setError(err.normalized?.message || err.message || "Could not load supplier orders.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <Spinner label="Loading supplier orders" />;

  return (
    <section className="account-page supplier-page">
      <div className="account-section-title">
        <div>
          <p className="eyebrow">Supplier Portal</p>
          <h1>Orders</h1>
          <p>Only orders assigned to your supplier partner appear here.</p>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <div className="surface-panel supplier-table">
        <div className="supplier-table__head supplier-table__row">
          <span>Order</span>
          <span>Status</span>
          <span>Items</span>
          <span>Actions</span>
        </div>
        {orders.length ? orders.map((order) => (
          <div className="supplier-table__row" key={order.group_id || order.number}>
            <div>
              <strong>{order.number}</strong>
              <span>{formatDate(order.date_placed)}</span>
            </div>
            <div><span className="supplier-status supplier-status--pending_review">{formatStatus(order.status)}</span></div>
            <div>
              <strong>{Number(order.supplier_item_count || 0).toLocaleString()}</strong>
              <span>{money(order.supplier_total_incl_tax, order.currency)}</span>
            </div>
            <div className="supplier-table__actions">
              <Link className="secondary-button" to={`/supplier/orders/${order.number}`}>
                <MaterialIcon name="open_in_new" size={18} />
                View
              </Link>
            </div>
          </div>
        )) : (
          <div className="supplier-empty-state">
            <MaterialIcon name="receipt_long" size={28} />
            <strong>No assigned orders</strong>
            <span>New paid customer orders assigned to your products will appear here.</span>
          </div>
        )}
      </div>
    </section>
  );
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()) || "Pending";
}

function formatDate(value) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function money(value, currency = "KES") {
  if (value === null || value === undefined || value === "") return "No total";
  return `${currency || "KES"} ${Number(value).toLocaleString()}`;
}
