import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function AddressCard({
  address,
  loading = false,
  onEdit,
  onDelete,
  onDefaultShipping,
  onDefaultBilling,
  onUse
}) {
  const title = address.title || [address.first_name, address.last_name].filter(Boolean).join(" ") || "Saved address";
  const lines = [address.line1, address.line2, address.line3, address.line4, address.state, address.postcode, address.country_code]
    .filter(Boolean)
    .join(", ");

  return (
    <article className="address-card">
      <div className="address-card__head">
        <span><MaterialIcon name="location_on" size={20} /></span>
        <div>
          <strong>{title}</strong>
          <small>{address.phone_number || "No phone added"}</small>
        </div>
      </div>

      <p>{lines || "No address line added."}</p>

      <div className="address-card__badges">
        {address.is_default_for_shipping ? <em>Default delivery</em> : null}
        {address.is_default_for_billing ? <em>Default billing</em> : null}
      </div>

      <div className="address-card__actions">
        {onUse ? (
          <button className="primary-button" type="button" disabled={loading} onClick={() => onUse(address)}>
            Use
          </button>
        ) : null}
        {onEdit ? (
          <button className="secondary-button" type="button" disabled={loading} onClick={() => onEdit(address)}>
            Edit
          </button>
        ) : null}
        {onDefaultShipping && !address.is_default_for_shipping ? (
          <button className="secondary-button" type="button" disabled={loading} onClick={() => onDefaultShipping(address)}>
            Delivery
          </button>
        ) : null}
        {onDefaultBilling && !address.is_default_for_billing ? (
          <button className="secondary-button" type="button" disabled={loading} onClick={() => onDefaultBilling(address)}>
            Billing
          </button>
        ) : null}
        {onDelete ? (
          <button className="danger-link address-card__delete" type="button" disabled={loading} onClick={() => onDelete(address)} aria-label={`Delete ${title}`}>
            <MaterialIcon name="delete" size={18} />
          </button>
        ) : null}
      </div>
    </article>
  );
}
