import { useEffect, useMemo, useState } from "react";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const defaultAddress = {
  first_name: "",
  last_name: "",
  line1: "",
  line2: "",
  line3: "",
  line4: "Nairobi",
  state: "Nairobi",
  postcode: "00100",
  country_code: "KE",
  phone_number: "",
  notes: "",
  latitude: "",
  longitude: "",
  location_label: ""
};

export default function ShippingAddressForm({
  address,
  countries = [],
  saving = false,
  title = "Delivery details",
  description = "",
  icon = "location_on",
  submitLabel = "Save delivery details",
  requirePhone = true,
  onSubmit
}) {
  const [form, setForm] = useState(() => ({ ...defaultAddress, ...normalizeAddress(address) }));
  const [locationStatus, setLocationStatus] = useState("");

  useEffect(() => {
    setForm({ ...defaultAddress, ...normalizeAddress(address) });
  }, [address]);

  const countryOptions = useMemo(() => {
    if (!countries.length) return [{ code: "KE", name: "Kenya" }];
    return countries.map((country) => ({
      code: country.code || country.iso_3166_1_a2 || country.iso_code,
      name: country.name || country.printable_name || country.code
    }));
  }, [countries]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.({
      ...form,
      country_code: String(form.country_code || "KE").toUpperCase(),
      latitude: form.latitude === "" ? null : form.latitude,
      longitude: form.longitude === "" ? null : form.longitude,
      location_label: form.location_label || [form.line1, form.line4].filter(Boolean).join(", ")
    });
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationStatus("Location is not available in this browser.");
      return;
    }

    setLocationStatus("Finding your location...");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setForm((current) => ({
          ...current,
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
          location_label: current.location_label || [current.line1, current.line4].filter(Boolean).join(", ")
        }));
        setLocationStatus("Location pinned.");
      },
      () => setLocationStatus("Could not get your location. You can enter the coordinates manually."),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  }

  const hasPinnedLocation = form.latitude !== "" && form.longitude !== "";
  const mapUrl = hasPinnedLocation
    ? `https://www.google.com/maps?q=${encodeURIComponent(`${form.latitude},${form.longitude}`)}&output=embed`
    : "";

  return (
    <form className="checkout-card shipping-form" onSubmit={handleSubmit}>
      <div className="checkout-card__title">
        <span><MaterialIcon name={icon} size={20} /></span>
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
      </div>

      <div className="form-grid two">
        <label>
          <span>First name</span>
          <input name="first_name" value={form.first_name} onChange={updateField} required autoComplete="given-name" />
        </label>
        <label>
          <span>Last name</span>
          <input name="last_name" value={form.last_name} onChange={updateField} required autoComplete="family-name" />
        </label>
      </div>

      <label>
        <span>Phone number</span>
        <input name="phone_number" value={form.phone_number} onChange={updateField} required={requirePhone} placeholder="+254700000001" autoComplete="tel" />
      </label>

      <label>
        <span>Address</span>
        <input name="line1" value={form.line1} onChange={updateField} required placeholder="Street, building, road" autoComplete="address-line1" />
      </label>

      <div className="form-grid two">
        <label>
          <span>Apartment or floor</span>
          <input name="line2" value={form.line2} onChange={updateField} autoComplete="address-line2" />
        </label>
        <label>
          <span>Company / site</span>
          <input name="line3" value={form.line3} onChange={updateField} />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Town / city</span>
          <input name="line4" value={form.line4} onChange={updateField} required autoComplete="address-level2" />
        </label>
        <label>
          <span>County / state</span>
          <input name="state" value={form.state} onChange={updateField} autoComplete="address-level1" />
        </label>
      </div>

      <div className="form-grid two">
        <label>
          <span>Country</span>
          <select name="country_code" value={form.country_code} onChange={updateField} required>
            {countryOptions.map((country) => (
              <option key={country.code} value={country.code}>{country.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Postcode</span>
          <input name="postcode" value={form.postcode} onChange={updateField} autoComplete="postal-code" />
        </label>
      </div>

      <label>
        <span>Delivery note</span>
        <textarea name="notes" value={form.notes} onChange={updateField} rows="3" placeholder="Gate, landmark, receiving instructions" />
      </label>

      <section className="delivery-location-picker">
        <div>
          <h3>Pin delivery location</h3>
        </div>
        <button className="secondary-button" type="button" onClick={useCurrentLocation}>
          <MaterialIcon name="my_location" size={18} />
          Use my current location
        </button>
        <div className="form-grid two">
          <label>
            <span>Latitude</span>
            <input name="latitude" value={form.latitude} onChange={updateField} inputMode="decimal" placeholder="-1.292066" />
          </label>
          <label>
            <span>Longitude</span>
            <input name="longitude" value={form.longitude} onChange={updateField} inputMode="decimal" placeholder="36.821946" />
          </label>
        </div>
        <label>
          <span>Location label</span>
          <input name="location_label" value={form.location_label} onChange={updateField} placeholder="Main gate, site entrance, shop front" />
        </label>
        {locationStatus ? <p className="location-status">{locationStatus}</p> : null}
        {hasPinnedLocation ? (
          <iframe
            className="delivery-location-map"
            title="Pinned delivery location"
            src={mapUrl}
            loading="lazy"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
          />
        ) : null}
      </section>

      <button className="primary-button checkout-submit" type="submit" disabled={saving}>
        <MaterialIcon name="check" size={19} />
        {saving ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}

function normalizeAddress(address) {
  if (!address) return {};
  const location = address.location || {};
  return {
    ...address,
    latitude: location.latitude ?? address.latitude ?? "",
    longitude: location.longitude ?? address.longitude ?? "",
    location_label: location.label ?? address.location_label ?? ""
  };
}
