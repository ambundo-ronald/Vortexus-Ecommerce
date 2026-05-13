import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import OrderDetailCard from "../../components/account/OrderDetailCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import "./guestOrder.css";

export default function GuestOrderDetailPage() {
  const { orderNumber, hash } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    storefrontExtrasApi.orders.guestDetail(orderNumber, hash)
      .then((payload) => {
        if (active) setOrder(payload?.order || null);
      })
      .catch((requestError) => {
        if (!active) return;
        const message = requestError?.normalized?.status === 404
          ? "This tracking link is invalid or has expired."
          : normalizeApiError(requestError, "Could not load this order.").message;
        setError(message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [hash, orderNumber]);

  return (
    <section className="guest-order-page guest-order-page--detail">
      <Link className="back-link" to="/orders/track">
        <MaterialIcon name="arrow_back" size={18} /> Track another order
      </Link>

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading order" /> : null}
      {!loading && order ? <OrderDetailCard order={order} /> : null}
    </section>
  );
}
