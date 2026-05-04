import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import OrderDetailCard from "../../components/account/OrderDetailCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useOrders } from "../../hooks/useOrders";

export default function OrderDetailPage() {
  const navigate = useNavigate();
  const { orderNumber } = useParams();
  const { order, loading, saving, error, loadOrder, reorder } = useOrders({ auto: false });

  useEffect(() => {
    if (orderNumber) void loadOrder(orderNumber);
  }, [loadOrder, orderNumber]);

  async function handleReorder(number) {
    await reorder(number);
    navigate("/checkout/cart");
  }

  return (
    <section className="account-page">
      <Link className="back-link" to="/account/orders">
        <MaterialIcon name="arrow_back" size={18} /> Orders
      </Link>
      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading order" /> : <OrderDetailCard order={order} saving={saving} onReorder={handleReorder} />}
    </section>
  );
}
