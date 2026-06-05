import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import ProductCard from "../../components/catalog/ProductCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import { productId, productTitle } from "../../utils/productDisplay";
import "./preferences.css";

export default function RecentlyViewedPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.account.recentlyViewed();
      setProducts(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load recently viewed products.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProducts();
  }, [loadProducts]);

  return (
    <section className="account-page preferences-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="preferences-hero">
        <div>
          <p className="eyebrow">Recently viewed</p>
          <h1>Products you viewed</h1>
          <p>Continue comparing items you opened recently.</p>
        </div>
        <button className="secondary-button" type="button" disabled={loading} onClick={() => void loadProducts()}>
          <MaterialIcon name="refresh" size={18} />
          Refresh
        </button>
      </div>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading recently viewed products" /> : null}

      {!loading && !products.length ? (
        <EmptyState
          title="No recently viewed products"
          message="Open a product detail page and it will appear here."
        />
      ) : null}

      {products.length ? (
        <div className="recent-products-grid">
          {products.map((product) => (
            <ProductCard product={product} key={productId(product) || productTitle(product)} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
