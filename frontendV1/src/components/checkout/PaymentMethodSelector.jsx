import { useEffect, useMemo, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { paymentMethodCopy } from "../../utils/payment";

const preferredOrder = ["mpesa", "pesapal", "bank_transfer", "credit_card", "debit_card", "cash_on_delivery", "airtel_money"];
const paymentLogoBase = "/payment methods logos";
const paymentLogos = {
  mpesa: `${paymentLogoBase}/M-PESA logo vector.jpeg`,
  pesapal: `${paymentLogoBase}/M-PESA logo vector.jpeg`,
  airtel_money: `${paymentLogoBase}/airtel money.jpeg`,
  bank_transfer: `${paymentLogoBase}/bank transfer.jpeg`,
  credit_card: `${paymentLogoBase}/visa mastercards.jpeg`,
  debit_card: `${paymentLogoBase}/visa mastercards.jpeg`,
  cash_on_delivery: `${paymentLogoBase}/cash on delivery.png`,
  footer: `${paymentLogoBase}/image showing all payment methods for footer.jpeg`
};

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
  const selectedDisplay = paymentDisplay(selected);
  const requiresPhone = Boolean(selected?.requires_phone || method === "mpesa" || method === "airtel_money");
  const isCard = method === "credit_card" || method === "debit_card";
  const submitCopy = paymentSubmitLabel(method, submitLabel);

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
      <div className="payment-form__intro">
        <h2>Payment</h2>
        <p>Choose a payment method and complete your order securely</p>
      </div>

      {!sortedMethods.length ? (
        <div className="checkout-note-panel">
          <MaterialIcon name="info" size={18} />
          <span>No payment methods are available right now.</span>
        </div>
      ) : null}

      <section className="payment-method-panel">
        <div className="payment-section-heading">
          <MaterialIcon name="credit_card" size={18} />
          <strong>Select payment method</strong>
        </div>
        <div className="payment-method-grid">
        {sortedMethods.map((item) => {
          const display = paymentDisplay(item);
          return (
            <button
              className={`payment-method-card ${method === item.code ? "active" : ""}`}
              type="button"
              key={item.code}
              aria-label={`${display.title} ${display.subtitle}`}
              onClick={() => setMethod(item.code)}
            >
              {display.badge || item.is_sandbox ? (
                <em className={item.is_sandbox ? "muted" : ""}>
                  {item.is_sandbox ? "Test" : display.badge}
                </em>
              ) : null}
              <span className="payment-method-card__icon">
                {display.logo ? (
                  <img src={display.logo} alt="" loading="lazy" />
                ) : (
                  <MaterialIcon name={display.icon} size={34} />
                )}
              </span>
              <span className="payment-method-card__copy">
                {!display.logo ? <strong>{display.title}</strong> : null}
                <small>{display.subtitle}</small>
              </span>
              <span className="payment-method-card__radio" aria-hidden="true" />
            </button>
          );
        })}
        </div>
      </section>

      {selected ? (
        <section className="payment-details-panel">
          <div className="payment-section-heading">
            <MaterialIcon name="phone_iphone" size={18} />
            <strong>Payment details</strong>
          </div>
          <div className="payment-details-box">
            <div>
              <h3>{selectedDisplay.detailTitle}</h3>
              <p>{selectedDisplay.detailCopy}</p>
            </div>

            {requiresPhone ? (
              <div className="payment-phone-row">
                <span className="payment-country-code">+254</span>
                <input type="tel" value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} required placeholder="7XX XXX XXX" />
              </div>
            ) : null}

            <label className="payment-email-field">
              <span>Email for receipt</span>
              <input type="email" value={payerEmail} onChange={(event) => setPayerEmail(event.target.value)} placeholder="you@example.com" required />
            </label>

            {isCard ? (
              <>
                <label className="payment-email-field">
                  <span>Name on card</span>
                  <input value={holderName} onChange={(event) => setHolderName(event.target.value)} placeholder="Cardholder name" required />
                </label>
                <div className="payment-info-strip warning">
                  <MaterialIcon name="science" size={17} />
                  <span>This backend currently exposes a sandbox card token flow. No real card details will be collected or charged.</span>
                </div>
              </>
            ) : null}

            {selected?.is_sandbox && !isCard ? (
              <div className="payment-info-strip warning">
                <MaterialIcon name="science" size={17} />
                <span>{selectedCopy.shortName} is connected to a sandbox environment and will not collect real money.</span>
              </div>
            ) : null}

            {requiresPhone ? (
              <div className="payment-info-strip">
                <MaterialIcon name="info" size={17} />
                <span>Please ensure your mobile money number is active and has sufficient balance.</span>
              </div>
            ) : null}

            <button className="primary-button checkout-submit payment-submit" type="submit" disabled={processing || !method}>
              <MaterialIcon name={requiresPhone ? "phone_iphone" : "shield_lock"} size={18} />
              {processing ? "Processing..." : submitCopy}
            </button>
          </div>
        </section>
      ) : null}

      <footer className="payment-trust-footer">
        <span>
          <MaterialIcon name="verified_user" size={18} />
          Your payment is protected with SSL encryption
        </span>
        <span className="payment-footer-brands">
          <img src={paymentLogos.footer} alt="Supported payment methods" loading="lazy" />
        </span>
      </footer>
    </form>
  );
}

function methodRank(code) {
  const index = preferredOrder.indexOf(code);
  return index === -1 ? preferredOrder.length + 1 : index;
}

function paymentDisplay(method = {}) {
  const code = method.code || "";
  const copy = paymentMethodCopy(method);
  const base = {
    title: method.name || copy.shortName,
    subtitle: copy.hint,
    detailTitle: method.name || copy.shortName,
    detailCopy: copy.hint,
    icon: copy.icon,
    badge: "",
    logo: paymentLogos[code] || ""
  };

  if (code === "mpesa" || code === "pesapal") {
    return {
      ...base,
      title: "M-Pesa",
      subtitle: "Instant STK Push",
      detailTitle: "M-Pesa STK Push",
      detailCopy: "You will receive an STK push on the phone number below to complete payment.",
      icon: "phone_iphone",
      badge: "Recommended",
      logo: paymentLogos[code] || paymentLogos.mpesa
    };
  }
  if (code === "bank_transfer") {
    return {
      ...base,
      title: "Bank Transfer",
      subtitle: "Direct to our account",
      detailTitle: "Bank transfer",
      detailCopy: "Use the payment reference after placing the order when making your transfer.",
      icon: "account_balance"
    };
  }
  if (code === "credit_card" || code === "debit_card") {
    return {
      ...base,
      title: "Credit / Debit Card",
      subtitle: "Visa, Mastercard",
      detailTitle: "Card payment",
      detailCopy: "Authorize your card securely to continue to order review.",
      icon: "credit_card",
      logo: paymentLogos[code]
    };
  }
  if (code === "cash_on_delivery") {
    return {
      ...base,
      title: "Cash on Delivery",
      subtitle: "Nairobi only",
      detailTitle: "Cash on delivery",
      detailCopy: "Pay when the order is delivered to your selected address.",
      icon: "payments"
    };
  }
  if (code === "airtel_money") {
    return {
      ...base,
      title: "Airtel Money",
      subtitle: "Mobile money prompt",
      detailTitle: "Airtel Money",
      detailCopy: "Approve the Airtel Money request on your phone to complete payment.",
      icon: "phone_iphone",
      logo: paymentLogos.airtel_money
    };
  }
  return base;
}

function paymentSubmitLabel(method, fallback) {
  if (method === "mpesa" || method === "pesapal") return "Receive STK Push";
  if (method === "airtel_money") return "Receive payment prompt";
  return fallback;
}
