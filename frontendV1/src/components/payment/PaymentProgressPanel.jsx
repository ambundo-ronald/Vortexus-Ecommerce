import MaterialIcon from "../ui/MaterialIcon.jsx";
import {
  isPaymentComplete,
  isPaymentFailed,
  paymentStatusView
} from "../../utils/payment";

export default function PaymentProgressPanel({
  payment,
  checking = false,
  onCheckStatus,
  onContinue,
  onChangeMethod
}) {
  if (!payment) return null;

  const view = paymentStatusView(payment);
  const complete = isPaymentComplete(payment);
  const failed = isPaymentFailed(payment);
  const providerReference =
    payment.external_reference ||
    payment.provider_payload?.checkout_request_id ||
    payment.provider_payload?.provider_reference ||
    "";

  return (
    <section className={`checkout-card payment-progress payment-progress--${view.tone}`} aria-live="polite">
      <div className="payment-progress__head">
        <span className="payment-progress__icon">
          <MaterialIcon name={view.icon} size={26} />
        </span>
        <div>
          <span className="payment-progress__eyebrow">{view.label}</span>
          <h2>{view.title}</h2>
          <p>{view.message}</p>
        </div>
      </div>

      <dl className="payment-progress__references">
        <div>
          <dt>Payment reference</dt>
          <dd>{payment.reference}</dd>
        </div>
        {providerReference ? (
          <div>
            <dt>Provider reference</dt>
            <dd>{providerReference}</dd>
          </div>
        ) : null}
      </dl>

      {!complete && !failed ? (
        <div className="payment-progress__waiting">
          <span className="payment-progress__pulse" />
          <span>{checking ? "Checking with the payment provider..." : "Waiting for provider confirmation"}</span>
        </div>
      ) : null}

      <div className="payment-progress__actions">
        {complete ? (
          <button className="primary-button" type="button" onClick={onContinue}>
            <MaterialIcon name="fact_check" size={19} />
            Review order
          </button>
        ) : (
          <button className="primary-button" type="button" disabled={checking} onClick={onCheckStatus}>
            <MaterialIcon name="sync" size={19} />
            {checking ? "Checking..." : failed ? "Check again" : "Check payment status"}
          </button>
        )}
        <button className="secondary-button" type="button" onClick={onChangeMethod}>
          <MaterialIcon name="swap_horiz" size={19} />
          {failed ? "Try another method" : "Change payment method"}
        </button>
      </div>
    </section>
  );
}
