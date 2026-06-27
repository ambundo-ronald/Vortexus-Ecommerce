import { Link } from "react-router-dom";

import Alert from "../ui/Alert.jsx";

export default function CheckoutErrorAlert({ error, fallback }) {
  const view = error || (fallback ? { tone: "danger", message: fallback } : null);
  if (!view?.message && !view?.title) return null;

  return (
    <Alert tone={view.tone || "danger"}>
      <div className="checkout-error-alert">
        {view.title ? <strong>{view.title}</strong> : null}
        {view.message ? <span>{view.message}</span> : null}
        {view.actionLabel && view.actionPath ? (
          <Link to={view.actionPath}>{view.actionLabel}</Link>
        ) : null}
      </div>
    </Alert>
  );
}
