import { Navigate, useLocation } from "react-router-dom";

import Spinner from "../components/ui/Spinner.jsx";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children, requireStaff = false }) {
  const location = useLocation();
  const { user, initialized } = useAuth();

  if (!initialized) return <Spinner label="Checking account" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (requireStaff && !user.is_staff) return <Navigate to="/unauthorized" replace />;
  return children;
}
