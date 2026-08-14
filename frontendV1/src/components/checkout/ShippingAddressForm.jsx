import { useEffect, useRef, useState } from "react";
import Swal from "sweetalert2";

import { checkoutApi } from "../../api/checkout.api";
import { trackStorefrontEvent } from "../../utils/analytics";
import MaterialIcon from "../ui/MaterialIcon.jsx";

const defaultAddress = {
  full_name: "",
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
  saving = false,
  title = "Delivery details",
  description = "",
  icon = "location_on",
  submitLabel = "Save delivery details",
  requirePhone = true,
  autoSubmitOnLocationChange = false,
  onSubmit
}) {
  const [form, setForm] = useState(() => ({ ...defaultAddress, ...normalizeAddress(address) }));
  const [locationStatus, setLocationStatus] = useState("");
  const [placeQuery, setPlaceQuery] = useState("");
  const [placeResults, setPlaceResults] = useState([]);
  const [placeSearching, setPlaceSearching] = useState(false);
  const lastAutoSubmitKeyRef = useRef("");
  const formStartedRef = useRef(false);

  useEffect(() => {
    setForm({ ...defaultAddress, ...normalizeAddress(address) });
  }, [address]);

  function updateField(event) {
    const { name, value } = event.target;
    if (!formStartedRef.current) {
      formStartedRef.current = true;
      trackStorefrontEvent("shipping_address_form_started", { source: name });
    }
    setForm((current) => ({ ...current, [name]: value }));
  }

  useEffect(() => {
    if (!autoSubmitOnLocationChange || saving || !isReadyForRateCalculation(form, requirePhone)) return undefined;

    const payload = buildSubmitPayload(form);
    const autoSubmitKey = [
      payload.latitude,
      payload.longitude,
      payload.line1,
      payload.line4,
      payload.country_code,
      payload.phone_number
    ].join("|");
    if (lastAutoSubmitKeyRef.current === autoSubmitKey) return undefined;

    const timeoutId = window.setTimeout(() => {
      lastAutoSubmitKeyRef.current = autoSubmitKey;
      onSubmit?.(payload);
    }, 700);

    return () => window.clearTimeout(timeoutId);
  }, [
    autoSubmitOnLocationChange,
    form,
    onSubmit,
    requirePhone,
    saving
  ]);

  function buildSubmitPayload(currentForm) {
    const deliveryLabel = currentForm.location_label || currentForm.location_formatted_address || placeQuery || currentForm.line3 || currentForm.line1 || "Delivery point";
    const town = currentForm.line4 || "Nairobi";
    const nameParts = splitFullName(currentForm.full_name || [currentForm.first_name, currentForm.last_name].filter(Boolean).join(" "));

    return {
      ...currentForm,
      first_name: nameParts.first_name,
      last_name: nameParts.last_name,
      line1: currentForm.line1 || deliveryLabel,
      line2: "",
      line4: town,
      state: currentForm.state || town,
      postcode: currentForm.postcode || "00100",
      country_code: String(currentForm.country_code || "KE").toUpperCase(),
      latitude: currentForm.latitude === "" ? null : currentForm.latitude,
      longitude: currentForm.longitude === "" ? null : currentForm.longitude,
      location_label: deliveryLabel,
      location_source: currentForm.location_source || "customer_pin",
      location_provider: currentForm.location_provider,
      location_place_id: currentForm.location_place_id,
      location_formatted_address: currentForm.location_formatted_address,
      location_confidence: normalizeConfidence(currentForm.location_confidence)
    };
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (!form.latitude || !form.longitude) {
      setLocationStatus("Pin the delivery location before saving.");
      trackStorefrontEvent("shipping_save_blocked", {
        reason: "missing_location",
        country_code: form.country_code || "KE",
        has_coordinates: false
      });
      void Swal.fire({
        icon: "warning",
        title: "Pin delivery location",
        text: "Please search and select the delivery location, or use your current location, before saving delivery details.",
        confirmButtonText: "OK",
        confirmButtonColor: "#2563eb"
      });
      return;
    }

    onSubmit?.(buildSubmitPayload(form));
  }

  function isReadyForRateCalculation(currentForm, phoneRequired) {
    const deliveryLabel = currentForm.line1 || currentForm.line3 || currentForm.location_label || currentForm.location_formatted_address || placeQuery;
    return Boolean(
      (currentForm.full_name || [currentForm.first_name, currentForm.last_name].filter(Boolean).join(" "))?.trim()
      && deliveryLabel?.trim()
      && currentForm.country_code?.trim()
      && (!phoneRequired || currentForm.phone_number?.trim())
      && currentForm.latitude !== ""
      && currentForm.longitude !== ""
    );
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationStatus("Location is not available in this browser.");
      trackStorefrontEvent("location_current_failed", { reason: "unsupported_browser" });
      return;
    }

    trackStorefrontEvent("location_current_requested", { source: "browser_geolocation" });
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
        trackStorefrontEvent("location_pinned", {
          source: "browser_geolocation",
          provider: "browser",
          has_coordinates: true
        });
      },
      () => {
        setLocationStatus("Could not get your location. You can enter the coordinates manually.");
        trackStorefrontEvent("location_current_failed", { reason: "permission_or_timeout" });
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  }

  async function searchDeliveryPlace() {
    const query = placeQuery.trim();
    if (!query) {
      setLocationStatus("Enter a place, road, building, or landmark to search.");
      return;
    }

    trackStorefrontEvent("location_search_started", {
      query_length: query.length,
      country_code: form.country_code || "KE"
    });
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
      trackStorefrontEvent("location_search_results", {
        query_length: query.length,
        country_code: form.country_code || "KE",
        result_count: Array.isArray(results) ? results.length : 0
      });
    } catch {
      setLocationStatus("Could not search places right now. You can still enter the coordinates manually.");
      setPlaceResults([]);
      trackStorefrontEvent("location_search_failed", {
        query_length: query.length,
        country_code: form.country_code || "KE"
      });
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
    trackStorefrontEvent("location_pinned", {
      source: "place_search",
      provider: place.provider || "",
      has_coordinates: latitude !== undefined && latitude !== null && longitude !== undefined && longitude !== null,
      country_code: form.country_code || "KE"
    });
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

      <label>
        <span>Name</span>
        <input name="full_name" value={form.full_name} onChange={updateField} required autoComplete="name" placeholder="Your name" />
      </label>

      <label>
        <span>Phone</span>
        <input name="phone_number" value={form.phone_number} onChange={updateField} required={requirePhone} placeholder="+254700000001" autoComplete="tel" />
      </label>

      <section className="delivery-location-picker">
        <div>
          <h3>Delivery location</h3>
        </div>
        <div className="delivery-location-search">
          <div className="delivery-location-search__form">
            <label>
              <span>Search and pin location</span>
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
        <details className="shipping-optional-details">
          <summary>Optional delivery details</summary>
          <div className="form-grid two">
            <label>
              <span>Company / site</span>
              <input name="line3" value={form.line3} onChange={updateField} placeholder="Company, site, office, or pickup point" />
            </label>
            <label>
              <span>Location label</span>
              <input name="location_label" value={form.location_label} onChange={updateField} placeholder="Main gate, site entrance, shop front" />
            </label>
          </div>
          <label>
            <span>Delivery note</span>
            <textarea name="notes" value={form.notes} onChange={updateField} rows="3" placeholder="Gate, landmark, receiving instructions" />
          </label>
        </details>
        <details className="delivery-location-advanced">
          <summary>Advanced coordinates</summary>
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
  const firstName = address.first_name || "";
  const lastName = address.last_name || "";
  const location = address.location || {};
  return {
    ...address,
    full_name: address.full_name || [firstName, lastName].filter(Boolean).join(" "),
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

function splitFullName(value) {
  const parts = String(value || "").trim().split(/\s+/).filter(Boolean);
  const firstName = parts.shift() || "Customer";
  return {
    first_name: firstName,
    last_name: parts.join(" ") || "Customer"
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
