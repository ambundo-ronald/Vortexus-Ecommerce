import { useEffect, useMemo, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { paymentMethodCopy } from "../../utils/payment";

const preferredOrder = ["pesapal", "cash_on_delivery", "bank_transfer", "credit_card", "debit_card", "mpesa", "airtel_money"];

export default function PaymentMethodSelector({
  methods = [],
  processing = false,
  onSubmit,
  submitLabel = "Continue to review",
  defaultEmail = "",
  defaultPhone = ""
}) {
  const sortedMethods = useMemo(() => {
    return [...methods].sort((a, b) => methodRank(a.code) - methodRank(b.code));
  }, [methods]);
  const [method, setMethod] = useState("");
  const [phoneNumber, setPhoneNumber] = useState(defaultPhone);
  const [payerEmail, setPayerEmail] = useState(defaultEmail);
  const [holderName, setHolderName] = useState("");

  useEffect(() => {
    if (!method && sortedMethods.length) {
      setMethod(sortedMethods[0].code);
    }
  }, [method, sortedMethods]);

  const selected = sortedMethods.find((item) => item.code === method);
  const selectedCopy = paymentMethodCopy(selected);
  const requiresPhone = Boolean(selected?.requires_phone || method === "mpesa" || method === "airtel_money");
  const isCard = method === "credit_card" || method === "debit_card";

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({
      method,
      phoneNumber,
      payerEmail,
      cardDetails: {
        holderName,
        paymentToken: method === "debit_card" ? "tok_test_debit" : "tok_test_visa",
        cardBrand: method === "debit_card" ? "debit" : "visa",
        last4: method === "debit_card" ? "0005" : "4242"
      }
    });
  }

  return (
    <form className="checkout-card payment-form" onSubmit={handleSubmit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name="payments" size={20} /></span>
        <div>
          <h2>Payment</h2>
        </div>
      </div>

      {!sortedMethods.length ? (
        <div className="checkout-note-panel">
          <MaterialIcon name="info" size={18} />
          <span>No payment methods are available right now.</span>
        </div>
      ) : null}

      <div className="choice-list">
        {sortedMethods.map((item) => {
          const copy = paymentMethodCopy(item);
          return (
            <button
              className={`choice-card ${method === item.code ? "active" : ""}`}
              type="button"
              key={item.code}
              onClick={() => setMethod(item.code)}
            >
              <span className="choice-card__icon">
                <MaterialIcon name={copy.icon} size={22} />
              </span>
              <span className="choice-card__copy">
                <strong>
                  {item.name}
                  <em className={item.is_sandbox ? "muted" : ""}>
                    {item.is_sandbox ? "Test" : item.requires_prepayment ? "Pay now" : "Pay later"}
                  </em>
                </strong>
                <small>{copy.hint}</small>
              </span>
              <MaterialIcon name={method === item.code ? "radio_button_checked" : "radio_button_unchecked"} size={22} />
            </button>
          );
        })}
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

      {isCard ? (
        <>
          <label>
            <span>Name on card</span>
            <input value={holderName} onChange={(event) => setHolderName(event.target.value)} placeholder="Cardholder name" required />
          </label>
          <div className="checkout-note-panel warning">
            <MaterialIcon name="science" size={18} />
            <span>This backend currently exposes a sandbox card token flow. No real card details will be collected or charged.</span>
          </div>
        </>
      ) : null}

      {selected?.is_sandbox && !isCard ? (
        <div className="checkout-note-panel warning">
          <MaterialIcon name="science" size={18} />
          <span>{selectedCopy.shortName} is connected to a sandbox environment and will not collect real money.</span>
        </div>
      ) : null}

      <button className="primary-button checkout-submit" type="submit" disabled={processing || !method}>
        <MaterialIcon name="shield_lock" size={19} />
        {processing ? "Processing..." : submitLabel}
      </button>
    </form>
  );
}

function methodRank(code) {
  const index = preferredOrder.indexOf(code);
  return index === -1 ? preferredOrder.length + 1 : index;
}
