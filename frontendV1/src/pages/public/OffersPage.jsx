import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import { formatDate } from "../../utils/formatDate";
import "./offers.css";

export default function OffersPage() {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadOffers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.offers.list();
      setOffers(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load offers.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOffers();
  }, [loadOffers]);

  return (
    <section className="offers-page">
      <div className="offers-hero">
        <div>
          <h1>Offers</h1>
        </div>
        <button className="secondary-button" type="button" disabled={loading} onClick={() => void loadOffers()}>
          <MaterialIcon name="refresh" size={18} />
          Refresh
        </button>
      </div>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading offers" /> : null}

      {!loading && !offers.length ? (
        <EmptyState title="No offers available" message="" />
      ) : null}

      {offers.length ? (
        <div className="offers-grid">
          {offers.map((offer) => (
            <OfferCard offer={offer} key={offer.id || offer.slug} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function OfferCard({ offer }) {
  const range = offer.benefit?.range || offer.condition?.range;

  return (
    <article className="offer-card">
      <span className="offer-card__icon">
        <MaterialIcon name="local_offer" size={24} />
      </span>
      <div className="offer-card__copy">
        <h2>{offer.name}</h2>
        {offer.description || offer.benefit?.description || offer.condition?.description ? (
          <p>{offer.description || offer.benefit?.description || offer.condition?.description}</p>
        ) : null}
      </div>
      <div className="offer-card__meta">
        {offer.end_datetime ? <span>Ends {formatDate(offer.end_datetime)}</span> : null}
        {range ? <span>{range.name}</span> : null}
      </div>
      <div className="offer-card__actions">
        <Link className="primary-button" to={`/offers/${offer.slug}`}>
          View offer
        </Link>
        {range?.slug ? (
          <Link className="secondary-button" to={`/catalog/ranges/${range.slug}`}>
            Shop range
          </Link>
        ) : null}
      </div>
    </article>
  );
}
