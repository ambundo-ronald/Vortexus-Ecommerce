import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function SupplierDashboardKPI({ icon, label, value, hint }) {
  return (
    <div className="supplier-kpi surface-panel">
      <span className="supplier-kpi__icon">
        <MaterialIcon name={icon} size={22} />
      </span>
      <div>
        <span>{label}</span>
        <strong>{value ?? 0}</strong>
        {hint ? <small>{hint}</small> : null}
      </div>
    </div>
  );
}
