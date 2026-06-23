import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import { formatDate } from "../../utils/formatDate";
import "./offers.css";

export default function OfferDetailPage() {
  const { offerSlug } = useParams();
  const [offer, setOffer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const range = useMemo(() => offer?.benefit?.range || offer?.condition?.range || null, [offer]);

  const loadOffer = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.offers.detail(offerSlug);
      setOffer(payload?.offer || payload);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load offer.").message);
    } finally {
      setLoading(false);
    }
  }, [offerSlug]);

  useEffect(() => {
    void loadOffer();
  }, [loadOffer]);

  return (
    <section className="offers-page">
      <Link className="back-link" to="/offers">
        <MaterialIcon name="arrow_back" size={18} /> Offers
      </Link>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading offer" /> : null}

      {!loading && !offer && !error ? (
        <EmptyState title="Offer not found" message="" />
      ) : null}

      {!loading && offer ? (
        <>
          <div className="offer-detail-hero">
            <span className="offer-detail-hero__icon">
              <MaterialIcon name="local_offer" size={30} />
            </span>
            <div>
              <h1>{offer.name}</h1>
              {offer.description ? <p>{offer.description}</p> : null}
            </div>
          </div>

          <div className="offer-detail-layout">
            <article className="offer-panel">
              <h2>How it works</h2>
              <RuleBlock title="Requirement" rule={offer.condition} fallback="" />
              <RuleBlock title="Benefit" rule={offer.benefit} fallback="" />
            </article>

            <aside className="offer-panel offer-summary">
              <h2>Offer details</h2>
              <SummaryRow label="Status" value={offer.status || "Open"} />
              <SummaryRow label="Starts" value={offer.start_datetime ? formatDate(offer.start_datetime, { time: true }) : "Already active"} />
              <SummaryRow label="Ends" value={offer.end_datetime ? formatDate(offer.end_datetime, { time: true }) : "No end date"} />
              <SummaryRow label="Exclusive" value={offer.exclusive ? "Yes" : "No"} />
              {range ? <SummaryRow label="Product range" value={range.name} /> : null}
              <div className="offer-summary__actions">
                {range?.slug ? (
                  <Link className="primary-button" to={`/catalog/ranges/${range.slug}`}>
                    Shop this range
                  </Link>
                ) : (
                  <Link className="primary-button" to="/catalog">
                    Shop products
                  </Link>
                )}
                {offer.redirect_url ? (
                  <Link className="secondary-button" to={offer.redirect_url}>
                    Open offer link
                  </Link>
                ) : null}
              </div>
            </aside>
          </div>
        </>
      ) : null}
    </section>
  );
}

function RuleBlock({ title, rule, fallback }) {
  const description = rule?.description || fallback;
  return (
    <section className="offer-rule">
      <span>{title}</span>
      <strong>{rule?.name || readable(rule?.type) || title}</strong>
      {description ? <p>{description}</p> : null}
    </section>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="offer-summary__row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function readable(value = "") {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
