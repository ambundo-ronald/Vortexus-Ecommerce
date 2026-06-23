import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import "./offers.css";

export default function RangeDetailPage() {
  const { rangeSlug } = useParams();
  const [range, setRange] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRange = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.offers.range(rangeSlug);
      setRange(payload?.range || null);
      setProducts(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load product range.").message);
    } finally {
      setLoading(false);
    }
  }, [rangeSlug]);

  useEffect(() => {
    void loadRange();
  }, [loadRange]);

  return (
    <section className="offers-page">
      <Link className="back-link" to="/offers">
        <MaterialIcon name="arrow_back" size={18} /> Offers
      </Link>

      <div className="range-hero">
        <div>
          <h1>{range?.name || "Range products"}</h1>
          {range?.description ? <p>{range.description}</p> : null}
        </div>
        <Link className="secondary-button" to="/catalog">
          Browse all
        </Link>
      </div>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading range products" /> : null}

      {!loading && !products.length ? (
        <EmptyState title="No products found" message="" />
      ) : null}

      {products.length ? <ProductGrid products={products} loading={loading} skeletonCount={8} /> : null}
    </section>
  );
}
