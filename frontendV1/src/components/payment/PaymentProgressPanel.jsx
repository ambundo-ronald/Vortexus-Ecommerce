import MaterialIcon from "../ui/MaterialIcon.jsx";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE,
  isPaymentComplete,
  isPaymentFailed,
  paymentStatusView
} from "../../utils/payment";

export default function PaymentProgressPanel({
  payment,
  checking = false,
  timedOut = false,
  remainingSeconds = null,
  onCheckStatus,
  onPromptAgain,
  onContinue,
  onChangeMethod
}) {
  if (!payment) return null;

  const view = paymentStatusView(payment);
  const complete = isPaymentComplete(payment);
  const failed = isPaymentFailed(payment);
  const shouldPromptAgain = timedOut && !complete && !failed;
  const minutesLeft = typeof remainingSeconds === "number" ? Math.floor(Math.max(0, remainingSeconds) / 60) : null;
  const secondsLeft = typeof remainingSeconds === "number" ? Math.max(0, remainingSeconds) % 60 : null;
  const countdownLabel = minutesLeft === null ? "" : `${minutesLeft}:${String(secondsLeft).padStart(2, "0")}`;
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
        <div className={`payment-progress__waiting${shouldPromptAgain ? " payment-progress__waiting--timeout" : ""}`}>
          <span className="payment-progress__pulse" />
          <span>
            {shouldPromptAgain
              ? PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE.replace(" or choose another method.", "")
              : checking
                ? "Checking with the payment provider..."
                : countdownLabel
                  ? `Waiting for provider confirmation · ${countdownLabel} remaining`
                  : "Waiting for provider confirmation"}
          </span>
        </div>
      ) : null}

      <div className="payment-progress__actions">
        {complete ? (
          <button className="primary-button" type="button" onClick={onContinue}>
            <MaterialIcon name="fact_check" size={19} />
            Review order
          </button>
        ) : (
          <button
            className="primary-button"
            type="button"
            disabled={checking}
            onClick={shouldPromptAgain && onPromptAgain ? onPromptAgain : onCheckStatus}
          >
            <MaterialIcon name={shouldPromptAgain ? "replay" : "sync"} size={19} className={checking ? "payment-progress__spin" : ""} />
            {checking ? "Checking..." : shouldPromptAgain ? "Prompt again" : failed ? "Check again" : "Check payment status"}
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
