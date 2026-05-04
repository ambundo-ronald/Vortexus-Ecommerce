import { useEffect, useMemo, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const preferredOrder = ["cash_on_delivery", "bank_transfer", "credit_card", "debit_card", "mpesa", "airtel_money"];

const methodIcons = {
  cash_on_delivery: "payments",
  bank_transfer: "account_balance",
  credit_card: "credit_card",
  debit_card: "credit_card",
  mpesa: "phone_iphone",
  airtel_money: "phone_iphone"
};

const reliableMethods = new Set(["cash_on_delivery", "bank_transfer", "credit_card", "debit_card"]);

export default function PaymentMethodSelector({ methods = [], processing = false, onSubmit }) {
  const sortedMethods = useMemo(() => {
    return [...methods].sort((a, b) => methodRank(a.code) - methodRank(b.code));
  }, [methods]);
  const [method, setMethod] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [payerEmail, setPayerEmail] = useState("");

  useEffect(() => {
    if (!method && sortedMethods.length) {
      setMethod(sortedMethods[0].code);
    }
  }, [method, sortedMethods]);

  const selected = sortedMethods.find((item) => item.code === method);
  const requiresPhone = Boolean(selected?.requires_phone || method === "mpesa" || method === "airtel_money");
  const gatewayDependent = selected && !reliableMethods.has(selected.code);

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({ method, phoneNumber, payerEmail });
  }

  return (
    <form className="checkout-card payment-form" onSubmit={handleSubmit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name="payments" size={20} /></span>
        <div>
          <h2>Payment</h2>
          <p>Select a payment option.</p>
        </div>
      </div>

      {!sortedMethods.length ? (
        <div className="checkout-note-panel">
          <MaterialIcon name="info" size={18} />
          <span>No payment methods are available right now.</span>
        </div>
      ) : null}

      <div className="choice-list">
        {sortedMethods.map((item) => (
          <button
            className={`choice-card ${method === item.code ? "active" : ""}`}
            type="button"
            key={item.code}
            onClick={() => setMethod(item.code)}
          >
            <span className="choice-card__icon">
              <MaterialIcon name={methodIcons[item.code] || "payments"} size={22} />
            </span>
            <span className="choice-card__copy">
              <strong>
                {item.name}
                {reliableMethods.has(item.code) ? <em>Ready</em> : <em className="muted">Mobile</em>}
              </strong>
              <small>{paymentHint(item)}</small>
            </span>
            <MaterialIcon name={method === item.code ? "radio_button_checked" : "radio_button_unchecked"} size={22} />
          </button>
        ))}
      </div>

      {requiresPhone ? (
        <label>
          <span>Phone number</span>
          <input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} required placeholder="+254700000001" />
        </label>
      ) : null}

      <label>
        <span>Email for receipt</span>
        <input type="email" value={payerEmail} onChange={(event) => setPayerEmail(event.target.value)} placeholder="you@example.com" required />
      </label>

      {(method === "credit_card" || method === "debit_card") ? (
        <div className="checkout-note-panel">
          <MaterialIcon name="lock" size={18} />
          <span>Card authorization is protected. No card number is stored in this browser.</span>
        </div>
      ) : null}

      {gatewayDependent ? (
        <div className="checkout-note-panel warning">
          <MaterialIcon name="warning" size={18} />
          <span>This option may be temporarily unavailable. If it fails, choose cash, bank transfer, or card.</span>
        </div>
      ) : null}

      <button className="primary-button checkout-submit" type="submit" disabled={processing || !method}>
        <MaterialIcon name="shield_lock" size={19} />
        {processing ? "Processing..." : "Place order"}
      </button>
    </form>
  );
}

function methodRank(code) {
  const index = preferredOrder.indexOf(code);
  return index === -1 ? preferredOrder.length + 1 : index;
}

function paymentHint(method) {
  if (method.code === "cash_on_delivery") return "Pay when your order arrives";
  if (method.code === "bank_transfer") return "Order is reserved for transfer";
  if (method.code === "credit_card" || method.code === "debit_card") return "Secure card authorization";
  if (method.requires_prepayment) return "Pay before order is placed";
  return "Available for this order";
}
