import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import AddressCard from "../../components/account/AddressCard.jsx";
import AddressForm from "../../components/account/AddressForm.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { normalizeApiError } from "../../utils/errorHandler";

export default function AddressesPage() {
  const notify = useUiStore((state) => state.notify);
  const [addresses, setAddresses] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadAddresses = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.addresses.list();
      setAddresses(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load addresses.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAddresses();
  }, [loadAddresses]);

  async function saveAddress(address) {
    setSaving(true);
    setError("");
    try {
      if (editing?.id) {
        await storefrontExtrasApi.addresses.update(editing.id, address);
        notify({ title: "Address updated", message: "Saved address details were updated.", icon: "task_alt" });
      } else {
        await storefrontExtrasApi.addresses.create(address);
        notify({ title: "Address added", message: "The address is ready for checkout.", icon: "task_alt" });
      }
      setEditing(null);
      setShowForm(false);
      await loadAddresses();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not save address.").message);
    } finally {
      setSaving(false);
    }
  }

  async function removeAddress(address) {
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.addresses.remove(address.id);
      notify({ title: "Address removed", message: "The saved address was deleted.", icon: "delete" });
      await loadAddresses();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not remove address.").message);
    } finally {
      setSaving(false);
    }
  }

  async function setDefault(address, type) {
    setSaving(true);
    setError("");
    try {
      if (type === "shipping") await storefrontExtrasApi.addresses.setDefaultShipping(address.id);
      if (type === "billing") await storefrontExtrasApi.addresses.setDefaultBilling(address.id);
      notify({ title: "Default updated", message: "Your address preference was saved.", icon: "task_alt" });
      await loadAddresses();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not update default address.").message);
    } finally {
      setSaving(false);
    }
  }

  function startCreate() {
    setEditing(null);
    setShowForm(true);
  }

  function startEdit(address) {
    setEditing(address);
    setShowForm(true);
  }

  return (
    <section className="account-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="account-section-title">
        <div>
          <p className="eyebrow">Address book</p>
          <h1>Saved addresses</h1>
        </div>
        <button className="primary-button account-inline-action" type="button" onClick={startCreate}>
          <MaterialIcon name="add" size={18} />
          Add
        </button>
      </div>

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading addresses" /> : null}

      {showForm ? (
        <AddressForm
          address={editing}
          loading={saving}
          title={editing ? "Edit address" : "New address"}
          submitLabel={editing ? "Save changes" : "Add address"}
          onSubmit={saveAddress}
          onCancel={() => {
            setEditing(null);
            setShowForm(false);
          }}
        />
      ) : null}

      {!loading && !addresses.length && !showForm ? (
        <EmptyState
          title="No saved addresses"
          message="Add delivery and billing addresses to make checkout faster."
        />
      ) : null}

      {addresses.length ? (
        <div className="address-grid">
          {addresses.map((address) => (
            <AddressCard
              key={address.id}
              address={address}
              loading={saving}
              onEdit={startEdit}
              onDelete={removeAddress}
              onDefaultShipping={(item) => setDefault(item, "shipping")}
              onDefaultBilling={(item) => setDefault(item, "billing")}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}
