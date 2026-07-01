import { useEffect, useMemo, useState } from "react";

import { checkoutApi } from "../../api/checkout.api";
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
  location_label: "",
  location_source: "",
  location_provider: "",
  location_place_id: "",
  location_formatted_address: "",
  location_confidence: ""
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
  const [placeQuery, setPlaceQuery] = useState("");
  const [placeResults, setPlaceResults] = useState([]);
  const [placeSearching, setPlaceSearching] = useState(false);

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
      location_label: form.location_label || [form.line1, form.line4].filter(Boolean).join(", "),
      location_source: form.location_source || "customer_pin",
      location_provider: form.location_provider,
      location_place_id: form.location_place_id,
      location_formatted_address: form.location_formatted_address,
      location_confidence: normalizeConfidence(form.location_confidence)
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
          location_label: current.location_label || [current.line1, current.line4].filter(Boolean).join(", "),
          location_source: "browser_geolocation",
          location_provider: "browser",
          location_place_id: "",
          location_formatted_address: current.location_formatted_address || "",
          location_confidence: position.coords.accuracy ? String(Math.max(0, Math.min(1, 1 - position.coords.accuracy / 5000)).toFixed(2)) : ""
        }));
        setLocationStatus("Location pinned.");
      },
      () => setLocationStatus("Could not get your location. You can enter the coordinates manually."),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  }

  async function searchDeliveryPlace() {
    const query = placeQuery.trim();
    if (!query) {
      setLocationStatus("Enter a place, road, building, or landmark to search.");
      return;
    }

    setPlaceSearching(true);
    setLocationStatus("Searching for that place...");
    try {
      const payload = await checkoutApi.searchPlaces({
        q: query,
        country_code: form.country_code || "KE",
        limit: 6
      });
      const results = payload?.results || [];
      setPlaceResults(Array.isArray(results) ? results : []);
      setLocationStatus(results.length ? "Choose the delivery place from the results." : "No place found. Try a nearby road, building, or town.");
    } catch {
      setLocationStatus("Could not search places right now. You can still enter the coordinates manually.");
      setPlaceResults([]);
    } finally {
      setPlaceSearching(false);
    }
  }

  function choosePlace(place) {
    const label = place.label || place.formatted_address || place.display_name || place.name || placeQuery;
    const addressInfo = place.address || {};
    const city = addressInfo.city || addressInfo.town || addressInfo.village || addressInfo.county || form.line4;
    const county = addressInfo.state || addressInfo.county || form.state;
    const postcode = addressInfo.postcode || form.postcode;
    const latitude = place.latitude ?? place.lat;
    const longitude = place.longitude ?? place.lon;

    setForm((current) => ({
      ...current,
      line1: current.line1 || compactLocationLabel(addressInfo, label),
      line4: city || current.line4,
      state: county || current.state,
      postcode: postcode || current.postcode,
      latitude: Number(latitude).toFixed(6),
      longitude: Number(longitude).toFixed(6),
      location_label: label,
      location_source: "place_search",
      location_provider: place.provider || "",
      location_place_id: place.place_id || "",
      location_formatted_address: place.formatted_address || label,
      location_confidence: normalizeConfidence(place.confidence) ?? ""
    }));
    setPlaceQuery(label);
    setPlaceResults([]);
    setLocationStatus("Delivery location pinned.");
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
        <div className="delivery-location-search">
          <div className="delivery-location-search__form">
            <label>
              <span>Search delivery place</span>
              <input
                value={placeQuery}
                onChange={(event) => setPlaceQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void searchDeliveryPlace();
                  }
                }}
                placeholder="Search estate, building, road, shop, landmark"
                autoComplete="off"
              />
            </label>
            <button className="secondary-button" type="button" disabled={placeSearching} onClick={() => void searchDeliveryPlace()}>
              <MaterialIcon name="search" size={18} />
              {placeSearching ? "Searching..." : "Search"}
            </button>
          </div>
          <button className="secondary-button" type="button" onClick={useCurrentLocation}>
            <MaterialIcon name="my_location" size={18} />
            Use my current location
          </button>
        </div>
        {placeResults.length ? (
          <div className="delivery-place-results" aria-label="Delivery place search results">
            {placeResults.map((place) => (
              <button key={place.place_id} type="button" onClick={() => choosePlace(place)}>
                <MaterialIcon name="location_on" size={17} />
                <span>{place.label || place.formatted_address}</span>
              </button>
            ))}
          </div>
        ) : null}
        <label>
          <span>Location label</span>
          <input name="location_label" value={form.location_label} onChange={updateField} placeholder="Main gate, site entrance, shop front" />
        </label>
        {locationStatus ? <p className="location-status">{locationStatus}</p> : null}
        {hasPinnedLocation ? (
          <div className="delivery-location-confirmed">
            <div className="delivery-location-confirmed__copy">
              <MaterialIcon name="task_alt" size={19} />
              <span>{form.location_label || "Delivery location pinned"}</span>
            </div>
            <iframe
              className="delivery-location-map"
              title="Pinned delivery location"
              src={mapUrl}
              loading="lazy"
              allowFullScreen
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>
        ) : null}
        <details className="delivery-location-advanced">
          <summary>Advanced location details</summary>
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
        </details>
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
    location_label: location.label ?? address.location_label ?? "",
    location_source: location.source ?? address.location_source ?? "",
    location_provider: location.provider ?? address.location_provider ?? "",
    location_place_id: location.place_id ?? address.location_place_id ?? "",
    location_formatted_address: location.formatted_address ?? address.location_formatted_address ?? "",
    location_confidence: location.confidence ?? address.location_confidence ?? ""
  };
}

function compactLocationLabel(addressInfo = {}, fallback = "") {
  return [
    addressInfo.road,
    addressInfo.suburb || addressInfo.neighbourhood,
    addressInfo.city || addressInfo.town || addressInfo.village
  ].filter(Boolean).join(", ") || fallback;
}

function normalizeConfidence(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return String(Math.max(0, Math.min(1, number)).toFixed(2));
}
