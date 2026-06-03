import { Link } from "react-router-dom";
import { useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useCartStore } from "../../store/cart.store";
import { formatCurrency } from "../../utils/currency";

export default function CartSummary({ basket }) {
  const [couponCode, setCouponCode] = useState("");
  const applyVoucher = useCartStore((state) => state.applyVoucher);
  const removeVoucher = useCartStore((state) => state.removeVoucher);
  const loading = useCartStore((state) => state.loading);
  const totals = basket?.totals || {};
  const vouchers = basket?.vouchers || [];
  const currency = totals.currency || basket?.currency || "KES";
  const subtotal = totals.subtotal ?? 0;
  const discount = Number(totals.discount || 0);
  const orderTotal =
    totals.order_total ??
    totals.total ??
    totals.total_incl_tax ??
    Math.max(0, Number(subtotal || 0) - discount);

  async function handleApplyCoupon(event) {
    event.preventDefault();
    const code = couponCode.trim();
    if (!code) return;
    try {
      await applyVoucher(code);
      setCouponCode("");
    } catch {
      // Store notification already explains why the coupon was not applied.
    }
  }

  return (
    <aside className="cart-summary surface-panel">
      <div className="cart-summary__head">
        <span>
          <MaterialIcon name="receipt_long" size={20} />
        </span>
        <div>
          <h2>Order summary</h2>
          <p>Review your cart before delivery</p>
        </div>
      </div>
      <div className="summary-group">
        <div className="summary-row">
          <span>Items</span>
          <strong>{basket?.item_count || 0}</strong>
        </div>
        <div className="summary-row">
          <span>Subtotal</span>
          <strong>{formatCurrency(subtotal, currency)}</strong>
        </div>
        {discount > 0 ? (
          <div className="summary-row summary-row--discount">
            <span>Coupon savings</span>
            <strong>-{formatCurrency(discount, currency)}</strong>
          </div>
        ) : null}
        <div className="summary-row summary-row--muted">
          <span>Delivery</span>
          <strong>Calculated next</strong>
        </div>
        <div className="summary-row summary-row--total">
          <span>Estimated total</span>
          <strong>{formatCurrency(orderTotal, currency)}</strong>
        </div>
      </div>
      <form className="coupon-form" onSubmit={(event) => void handleApplyCoupon(event)}>
        <label htmlFor="coupon-code">
          <MaterialIcon name="sell" size={16} />
          Coupon or promo code
        </label>
        <div>
          <input
            id="coupon-code"
            value={couponCode}
            placeholder="Enter code"
            disabled={loading}
            onChange={(event) => setCouponCode(event.target.value)}
          />
          <button className="secondary-button" type="submit" disabled={loading || !couponCode.trim()}>
            Apply
          </button>
        </div>
      </form>
      {vouchers.length ? (
        <div className="applied-coupons">
          {vouchers.map((voucher) => (
            <div className="applied-coupon" key={voucher.id}>
              <span>{voucher.code}</span>
              <button type="button" disabled={loading} onClick={() => void removeVoucher(voucher.id)} aria-label={`Remove ${voucher.code}`}>
                <MaterialIcon name="close" size={16} />
              </button>
            </div>
          ))}
        </div>
      ) : null}
      <Link className="primary-button" to="/checkout/shipping">
        <MaterialIcon name="lock" size={19} />
        Checkout securely
      </Link>
      <p className="cart-summary__safe-note">
        <MaterialIcon name="verified_user" size={17} />
        Secure checkout. Your data is protected.
      </p>
      <Link className="cart-summary__continue" to="/catalog">
        <MaterialIcon name="arrow_back" size={18} />
        Continue shopping
      </Link>
    </aside>
  );
}
