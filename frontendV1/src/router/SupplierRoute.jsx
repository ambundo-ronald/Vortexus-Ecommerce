import { Navigate } from "react-router-dom";
import Spinner from "../components/ui/Spinner.jsx";
import { useAuth } from "../hooks/useAuth";

export default function SupplierRoute({ children, user: providedUser, requireApproved = false }) {
  const { user: authUser, initialized } = useAuth();
  const user = providedUser || authUser;
  const supplier = user?.supplier;
  if (!initialized && !providedUser) return <Spinner label="Checking supplier access" />;
  if (!user) return <Navigate to="/login" replace />;
  if (!supplier?.is_supplier) return <Navigate to="/supplier/apply" replace />;
  if (requireApproved && supplier.status !== "approved") return <Navigate to="/supplier" replace />;
  return children;
}
