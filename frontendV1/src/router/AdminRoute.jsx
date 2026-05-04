import ProtectedRoute from "./ProtectedRoute.jsx";

export default function AdminRoute(props) {
  return <ProtectedRoute requireStaff {...props} />;
}
