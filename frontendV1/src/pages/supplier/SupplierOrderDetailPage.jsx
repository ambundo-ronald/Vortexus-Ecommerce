import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { supplierApi } from "../../api/supplier.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";

const fulfillmentStatuses = [
  { value: "processing", label: "Processing" },
  { value: "packed", label: "Packed" },
  { value: "shipped", label: "Shipped" },
  { value: "delivered", label: "Delivered" },
  { value: "cancelled", label: "Cancelled" }
];

export default function SupplierOrderDetailPage() {
  const { orderNumber } = useParams();
  const notify = useUiStore((state) => state.notify);
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadOrder = useCallback(async ({ silent = false } = {}) => {
    if (!orderNumber) return;
    if (!silent) setLoading(true);
    setError("");
    try {
      const payload = await supplierApi.order(orderNumber);
      setOrder(payload.order || payload);
    } catch (err) {
      setError(err.normalized?.message || err.message || "Could not load supplier order.");
    } finally {
      if (!silent) setLoading(false);
    }
  }, [orderNumber]);

  useEffect(() => {
    void loadOrder();
  }, [loadOrder]);

  if (loading) return <Spinner label="Loading supplier order" />;

  const lines = order?.lines || [];
  const totals = order?.supplier_totals || {};

  return (
    <section className="account-page supplier-page">
      <Link className="secondary-button account-inline-action" to="/supplier/orders">
        <MaterialIcon name="arrow_back" size={18} />
        Back to orders
      </Link>

      <div className="account-section-title">
        <div>
          <p className="eyebrow">Supplier Order</p>
          <h1>{order?.number || orderNumber}</h1>
          <p>{formatStatus(order?.status)} · {money(totals.total_incl_tax, order?.currency)}</p>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      {order ? (
        <div className="supplier-order-summary-grid">
          <div className="surface-panel supplier-order-summary">
            <MaterialIcon name="person" size={22} />
            <div>
              <span>Customer</span>
              <strong>{order.customer?.name || order.customer?.email || "Guest customer"}</strong>
              {order.customer?.email ? <small>{order.customer.email}</small> : null}
            </div>
          </div>
          <div className="surface-panel supplier-order-summary">
            <MaterialIcon name="local_shipping" size={22} />
            <div>
              <span>Delivery</span>
              <strong>{order.shipping_method || "Shipping method not recorded"}</strong>
              <small>{formatAddress(order.shipping_address)}</small>
            </div>
          </div>
          <div className="surface-panel supplier-order-summary">
            <MaterialIcon name="inventory" size={22} />
            <div>
              <span>Supplier items</span>
              <strong>{Number(totals.item_count || 0).toLocaleString()}</strong>
              <small>{order.tracking_reference || "No tracking reference yet"}</small>
            </div>
          </div>
        </div>
      ) : null}

      <div className="surface-panel supplier-table">
        <div className="supplier-table__head supplier-table__row">
          <span>Line</span>
          <span>Status</span>
          <span>Quantity</span>
          <span>Fulfillment</span>
        </div>
        {lines.length ? lines.map((line) => (
          <div className="supplier-table__row" key={line.id}>
            <div>
              <strong>{line.title || line.product?.title || "Order line"}</strong>
              <span>{line.upc || line.product?.upc || line.partner_sku || "No SKU"}</span>
            </div>
            <div><span className="supplier-status supplier-status--pending_review">{formatStatus(line.status)}</span></div>
            <div>
              <strong>{Number(line.quantity || 0).toLocaleString()}</strong>
              <span>{money(line.line_price_incl_tax, order?.currency)}</span>
            </div>
            <SupplierLineFulfillment
              line={line}
              order={order}
              orderNumber={order.number}
              notify={notify}
              onUpdated={() => loadOrder({ silent: true })}
            />
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

function SupplierLineFulfillment({ line, order, orderNumber, notify, onUpdated }) {
  const initialStatus = fulfillmentStatuses.some((item) => item.value === line.status) ? line.status : "processing";
  const [status, setStatus] = useState(initialStatus);
  const [trackingReference, setTrackingReference] = useState(order.tracking_reference || "");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setStatus(fulfillmentStatuses.some((item) => item.value === line.status) ? line.status : "processing");
    setTrackingReference(order.tracking_reference || "");
  }, [line.status, order.tracking_reference]);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await supplierApi.updateOrderLineStatus(orderNumber, line.id, {
        status,
        tracking_reference: trackingReference.trim(),
        note: note.trim()
      });
      notify({
        title: "Fulfillment updated",
        message: response?.detail || `${line.title || "Order line"} is now ${formatStatus(status)}.`,
        icon: "local_shipping"
      });
      setNote("");
      await onUpdated();
    } catch (err) {
      setError(err.normalized?.message || err.message || "Could not update this order line.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="supplier-order-line-form" onSubmit={submit}>
      <div className="supplier-order-line-form__row">
        <select aria-label={`Status for ${line.title || "order line"}`} value={status} onChange={(event) => setStatus(event.target.value)} disabled={saving}>
          {fulfillmentStatuses.map((item) => (
            <option value={item.value} key={item.value}>{item.label}</option>
          ))}
        </select>
        <button className="secondary-button" type="submit" disabled={saving}>
          <MaterialIcon name={saving ? "hourglass_top" : "sync"} size={17} />
          {saving ? "Saving" : "Update"}
        </button>
      </div>
      <input
        aria-label={`Tracking reference for ${line.title || "order line"}`}
        placeholder="Tracking reference"
        value={trackingReference}
        onChange={(event) => setTrackingReference(event.target.value)}
        disabled={saving}
      />
      <input
        aria-label={`Fulfillment note for ${line.title || "order line"}`}
        placeholder="Optional customer note"
        value={note}
        onChange={(event) => setNote(event.target.value)}
        disabled={saving}
      />
      {error ? <small className="supplier-order-line-form__error">{error}</small> : null}
    </form>
  );
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()) || "Pending";
}

function formatAddress(address) {
  if (!address) return "Delivery address not recorded";
  return [
    address.line1,
    address.line2,
    address.line3,
    address.line4,
    address.state,
    address.postcode
  ].filter(Boolean).join(", ") || "Delivery address not recorded";
}

function money(value, currency = "KES") {
  if (value === null || value === undefined || value === "") return "No total";
  return `${currency || "KES"} ${Number(value).toLocaleString()}`;
}
