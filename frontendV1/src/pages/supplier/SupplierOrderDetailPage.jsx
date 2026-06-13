import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { supplierApi } from "../../api/supplier.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";

export default function SupplierOrderDetailPage() {
  const { orderNumber } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const payload = await supplierApi.order(orderNumber);
        if (mounted) setOrder(payload.order || payload);
      } catch (err) {
        if (mounted) setError(err.normalized?.message || err.message || "Could not load supplier order.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    if (orderNumber) void load();
    return () => {
      mounted = false;
    };
  }, [orderNumber]);

  if (loading) return <Spinner label="Loading supplier order" />;

  const lines = order?.lines || order?.order?.lines || [];

  return (
    <section className="account-page supplier-page">
      <Link className="secondary-button account-inline-action" to="/supplier/orders">
        <MaterialIcon name="arrow_back" size={18} />
        Back to orders
      </Link>

      <div className="account-section-title">
        <div>
          <p className="eyebrow">Supplier Order</p>
          <h1>{order?.order_number || order?.number || orderNumber}</h1>
          <p>{formatStatus(order?.status)} · {money(order?.total_incl_tax, order?.currency)}</p>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <div className="surface-panel supplier-table">
        <div className="supplier-table__head supplier-table__row">
          <span>Line</span>
          <span>Status</span>
          <span>Quantity</span>
          <span>Total</span>
        </div>
        {lines.length ? lines.map((line) => (
          <div className="supplier-table__row" key={line.id}>
            <div>
              <strong>{line.title || line.product?.title || "Order line"}</strong>
              <span>{line.upc || line.product?.upc || line.partner_sku || "No SKU"}</span>
            </div>
            <div><span className="supplier-status supplier-status--pending_review">{formatStatus(line.status)}</span></div>
            <div><strong>{Number(line.quantity || 0).toLocaleString()}</strong></div>
            <div><strong>{money(line.line_price || line.line_price_incl_tax, order?.currency)}</strong></div>
          </div>
        )) : (
          <div className="supplier-empty-state">
            <MaterialIcon name="receipt_long" size={28} />
            <strong>No order lines found</strong>
          </div>
        )}
      </div>
    </section>
  );
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()) || "Pending";
}

function money(value, currency = "KES") {
  if (value === null || value === undefined || value === "") return "No total";
  return `${currency || "KES"} ${Number(value).toLocaleString()}`;
}
