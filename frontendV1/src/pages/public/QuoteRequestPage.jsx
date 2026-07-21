import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import QuoteRequestForm from "../../components/quotes/QuoteRequestForm.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { catalogApi } from "../../api/catalog.api";
import { quotesApi } from "../../api/quotes.api";
import { useAuth } from "../../hooks/useAuth";
import { useUiStore } from "../../store/ui.store";
import { productImageAlt, productImageUrl } from "../../utils/productImages";
import { productId as resolveProductId, productInitials, productPrice, productTitle } from "../../utils/productDisplay";

export default function QuoteRequestPage() {
  const [searchParams] = useSearchParams();
  const productId = searchParams.get("product");
  const { user } = useAuth();
  const [product, setProduct] = useState(null);
  const [loadingProduct, setLoadingProduct] = useState(Boolean(productId));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const notify = useUiStore((state) => state.notify);

  useEffect(() => {
    if (!productId) return undefined;
    let cancelled = false;
    async function loadProduct() {
      setLoadingProduct(true);
      setError("");
      try {
        const payload = await catalogApi.product(productId);
        if (!cancelled) setProduct(payload.product || null);
      } catch (requestError) {
        if (!cancelled) setError(requestError.normalized?.message || requestError.message || "Could not load product.");
      } finally {
        if (!cancelled) setLoadingProduct(false);
      }
    }
    void loadProduct();
    return () => {
      cancelled = true;
    };
  }, [productId]);

  const price = useMemo(() => (product ? productPrice(product) : null), [product]);
  const resolvedProductId = product ? resolveProductId(product) : "";
  const resolvedTitle = product ? productTitle(product) : "";
  const productImage = useMemo(() => (product ? productImageUrl(product) : ""), [product]);
  const productImageAltText = useMemo(() => (product ? productImageAlt(product, resolvedTitle) : resolvedTitle), [product, resolvedTitle]);

  async function submitQuote(payload) {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const response = await quotesApi.create(payload);
      const message = response.detail || "Quote request received. Our team will contact you shortly.";
      setSuccess(message);
      notify({ title: "Quote request sent", message, icon: "request_quote" });
    } catch (requestError) {
      const message = requestError.normalized?.message || requestError.message || "Could not submit quote request.";
      setError(message);
      notify({ tone: "danger", title: "Quote request failed", message });
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="quote-page">
      <Link className="back-link" to={resolvedProductId ? `/products/${resolvedProductId}` : "/catalog"}>
        <MaterialIcon name="arrow_back" size={18} />
        {product ? "Product" : "Catalog"}
      </Link>

      <Alert tone="success">{success}</Alert>
      <Alert>{error}</Alert>

      <div className="quote-layout">
        <aside className="quote-product surface-panel">
          {loadingProduct ? (
            <Spinner label="Loading product" />
          ) : product ? (
            <>
              {productImage ? (
                <img
                  src={productImage}
                  alt={productImageAltText}
                  loading="lazy"
                  decoding="async"
                  width="360"
                  height="280"
                />
              ) : <span className="quote-product__image-fallback">{productInitials(resolvedTitle)}</span>}
              <div>
                <span>Selected product</span>
                <h1>{resolvedTitle}</h1>
                <strong>{price?.label || "Quote on request"}</strong>
                {price?.sublabel ? <small>{price.sublabel}</small> : null}
              </div>
            </>
          ) : (
            <div>
              <span>General request</span>
              <h1>Tell us what you need</h1>
            </div>
          )}
        </aside>

        <QuoteRequestForm product={product} user={user} loading={saving} onSubmit={submitQuote} />
      </div>
    </section>
  );
}
