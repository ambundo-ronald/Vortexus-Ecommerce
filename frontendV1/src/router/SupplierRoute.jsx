import { Navigate } from "react-router-dom";

export default function SupplierRoute({ children, user }) {
  const supplier = user?.supplier;
  if (!user) return <Navigate to="/login" replace />;
  if (!supplier?.is_supplier) return <Navigate to="/unauthorized" replace />;
  return children;
}
