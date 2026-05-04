import { Link } from "react-router-dom";

import OrderHistoryList from "../../components/account/OrderHistoryList.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useOrders } from "../../hooks/useOrders";

export default function OrdersPage() {
  const { orders, pagination, loading, error } = useOrders();

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>
      <div className="account-section-title">
        <h1>Orders</h1>
        <p>{pagination?.total || 0} order{pagination?.total === 1 ? "" : "s"}</p>
      </div>
      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading orders" /> : <OrderHistoryList orders={orders} />}
    </section>
  );
}
