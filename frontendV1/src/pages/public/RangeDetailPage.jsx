import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import ProductGrid from "../../components/catalog/ProductGrid.jsx";
import BreadcrumbNav from "../../components/seo/BreadcrumbNav.jsx";
import Seo, { absoluteUrl } from "../../components/seo/Seo.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import { productTitle, productUrl } from "../../utils/productDisplay";
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

  const title = range?.name || titleFromSlug(rangeSlug);
  const canonicalPath = `/catalog/ranges/${rangeSlug}`;
  const description = cleanText(range?.description) || `Shop ${title.toLowerCase()} products and eligible range offers on Reesolmart.`;

  return (
    <section className="offers-page">
      <Seo
        title={`${title} range | Reesolmart`}
        description={description}
        canonicalPath={canonicalPath}
        jsonLd={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Offers", path: "/offers" },
            { name: title, path: canonicalPath }
          ]),
          itemListSchema(products)
        ]}
      />
      <Link className="back-link" to="/offers">
        <MaterialIcon name="arrow_back" size={18} /> Offers
      </Link>
      <BreadcrumbNav
        items={[
          { label: "Home", href: "/" },
          { label: "Offers", href: "/offers" },
          { label: title }
        ]}
      />

      <div className="range-hero">
        <div>
          <h1>{title}</h1>
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

function breadcrumbSchema(items) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path)
    }))
  };
}

function itemListSchema(products = []) {
  if (!products.length) return null;
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    itemListElement: products.slice(0, 24).map((product, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: productTitle(product),
      url: absoluteUrl(productUrl(product))
    }))
  };
}

function titleFromSlug(value = "") {
  return String(value || "Range products")
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function cleanText(value = "") {
  return String(value || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}
