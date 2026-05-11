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
      <h2>Order summary</h2>
      <div className="summary-row">
        <span>Items</span>
        <strong>{basket?.item_count || 0}</strong>
      </div>
      <div className="summary-row">
        <span>Subtotal</span>
        <strong>{formatCurrency(totals.subtotal, totals.currency)}</strong>
      </div>
      {Number(totals.discount || 0) > 0 ? (
        <div className="summary-row summary-row--discount">
          <span>Coupon savings</span>
          <strong>-{formatCurrency(totals.discount, totals.currency)}</strong>
        </div>
      ) : null}
      <form className="coupon-form" onSubmit={(event) => void handleApplyCoupon(event)}>
        <label htmlFor="coupon-code">Coupon code</label>
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
        <MaterialIcon name="local_shipping" size={19} />
        Continue to shipping
      </Link>
    </aside>
  );
}
