import { useEffect, useMemo, useState } from "react";
import { FaFacebookF, FaLinkedinIn, FaWhatsapp } from "react-icons/fa";
import { FaXTwitter } from "react-icons/fa6";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import ProductImageGallery from "../../components/catalog/ProductImageGallery.jsx";
import ProductAlertForm from "../../components/catalog/ProductAlertForm.jsx";
import ProductSpecifications from "../../components/catalog/ProductSpecifications.jsx";
import RelatedProducts from "../../components/catalog/RelatedProducts.jsx";
import BreadcrumbNav from "../../components/seo/BreadcrumbNav.jsx";
import ReviewList from "../../components/reviews/ReviewList.jsx";
import Seo, { absoluteUrl } from "../../components/seo/Seo.jsx";
import StarRating from "../../components/reviews/StarRating.jsx";
import Alert from "../../components/ui/Alert.jsx";
import Badge from "../../components/ui/Badge.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import WishlistButton from "../../components/wishlist/WishlistButton.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useProductDetail } from "../../hooks/useProductDetail";
import { useCartStore } from "../../store/cart.store";
import { useUiStore } from "../../store/ui.store";
import { useWishlistStore } from "../../store/wishlist.store";
import { searchAttributionMetadata, trackStorefrontEvent } from "../../utils/analytics";
import {
  productBrand,
  productCategory,
  productCategoryPath,
  productId as resolveProductId,
  productPrice,
  productRating,
  productSku,
  productTitle,
  productUrl,
  stockTone
} from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";
import "./ProductDetailPage.css";

export default function ProductDetailPage() {
  const { "*": routeProductPath = "" } = useParams();
  const routeProductRef = lastPathSegment(routeProductPath);
  const { product, related, loading, error } = useProductDetail(routeProductRef);
  const addItem = useCartStore((state) => state.addItem);
  const cartLoading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [optionError, setOptionError] = useState("");
  const [copiedShare, setCopiedShare] = useState(false);
  const [alertSaving, setAlertSaving] = useState(false);
  const [callbackOpen, setCallbackOpen] = useState(false);
  const [activeInfoTab, setActiveInfoTab] = useState("description");
  const [quantity, setQuantity] = useState(1);
  const productOptions = useMemo(() => product?.options || product?.product_options || [], [product]);
  const missingRequiredOptions = useMemo(
    () => productOptions.filter((option) => option.required && !selectedOptions[option.id || option.code]),
    [productOptions, selectedOptions]
  );
  const breadcrumbCategories = useMemo(() => productCategoryPath(product || {}), [product]);
  const category = useMemo(() => breadcrumbCategories[breadcrumbCategories.length - 1] || product?.categories?.[0] || null, [breadcrumbCategories, product]);
  const categoryLabel = productCategory(product || {}, "Uncategorized");
  const categoryHref = category ? `/catalog/category/${category.slug || category.id}` : "/catalog";
  const detailSpecs = useMemo(() => buildProductSpecs(product), [product]);
  const quickSpecs = useMemo(() => buildQuickSpecs(detailSpecs), [detailSpecs]);
  const overviewText = useMemo(() => cleanOverview(product?.description), [product?.description]);
  const productHighlights = useMemo(() => normalizeProductHighlights(product?.highlights), [product?.highlights]);
  const resolvedProductId = resolveProductId(product || {}) || routeProductRef;
  const resolvedTitle = productTitle(product || {});
  const resolvedSku = productSku(product || {}, "Pending");
  const shareUrl = useMemo(() => {
    const path = product ? productUrl(product) : `/products/${resolvedProductId || routeProductRef}`;
    if (typeof window === "undefined") return path;
    return new URL(path, window.location.origin).toString();
  }, [product, resolvedProductId, routeProductRef]);
  const breadcrumbItems = useMemo(() => {
    const categoryItems = breadcrumbCategories.length
      ? breadcrumbCategories.map((item) => ({
          label: item.name || item.title || categoryLabel,
          href: item.slug ? `/catalog/category/${item.slug}` : categoryHref
        }))
      : [{ label: categoryLabel, href: categoryHref }];

    return [
      { label: "Home", href: "/" },
      { label: "Shop", href: "/catalog" },
      ...categoryItems,
      { label: resolvedTitle }
    ];
  }, [breadcrumbCategories, categoryHref, categoryLabel, resolvedTitle]);

  useEffect(() => {
    if (user && resolvedProductId) void loadStatus([resolvedProductId]);
  }, [loadStatus, resolvedProductId, user]);

  useEffect(() => {
    setQuantity(1);
    setSelectedOptions({});
    setOptionError("");
  }, [product?.id]);

  useEffect(() => {
    if (!resolvedProductId || !product) return;
    trackStorefrontEvent("product_view", {
      ...searchAttributionMetadata(),
      product_id: resolvedProductId,
      product_title: resolvedTitle,
      path: productUrl(product)
    });
  }, [product, resolvedProductId, resolvedTitle]);

  if (loading) return <Spinner label="Loading product" />;
  if (error) return <Alert>{error}</Alert>;
  if (!product) return <Alert tone="warning">Product not found.</Alert>;

  const price = productPrice(product);
  const stock = stockTone(product);
  const canAddToCart = stock.isAvailable && !price.isQuote;
  const { rating, reviewCount } = productRating(product);
  const brandLabel = productBrand(product, "Not specified");
  const maxQuantity = stock.count > 0 ? stock.count : 99;
  const boundedQuantity = Math.max(1, Math.min(quantity, maxQuantity || 1));
  const canonicalPath = productUrl(product);
  const seoDescription = buildProductSeoDescription(product, resolvedTitle, brandLabel, categoryLabel);
  const seoImage = productImageUrl(product) || "/Reesolmart logo.png";
  const seoSchemas = buildProductSeoSchemas({
    product,
    title: resolvedTitle,
    description: seoDescription,
    canonicalPath,
    image: seoImage,
    price,
    stock,
    rating,
    reviewCount,
    brand: brandLabel,
    sku: resolvedSku,
    breadcrumbs: breadcrumbCategories
  });

  async function handleAddToCart() {
    if (!stock.isAvailable) {
      notify({
        tone: "warning",
        title: "Sold out",
        message: `${resolvedTitle} is out of stock right now.`
      });
      return;
    }
    if (price.isQuote) {
      notify({
        tone: "warning",
        title: "Price unavailable",
        message: "Request a quote for this product before checkout."
      });
      return;
    }
    if (missingRequiredOptions.length) {
      setOptionError(`Choose ${missingRequiredOptions.map((option) => option.name || option.code).join(", ")} before adding to cart.`);
      return;
    }
    try {
      setOptionError("");
      const options = productOptions
        .map((option) => ({
          option_id: option.id || option.option_id,
          code: option.code,
          value: selectedOptions[option.id || option.code] || ""
        }))
        .filter((option) => option.value !== "");
      await addItem(resolvedProductId, boundedQuantity, options, searchAttributionMetadata({
        product_id: Number(resolvedProductId),
        product_title: resolvedTitle
      }));
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  async function handleNativeShare() {
    const payload = {
      title: resolvedTitle,
      text: `View ${resolvedTitle} on Reesolmart`,
      url: shareUrl
    };
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share(payload);
        return;
      } catch (shareError) {
        if (shareError?.name === "AbortError") return;
      }
    }
    await handleCopyShare();
  }

  async function handleCopyShare() {
    try {
      if (!navigator.clipboard) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(shareUrl);
      setCopiedShare(true);
      notify({ title: "Link copied", message: "Product link is ready to share.", icon: "content_copy" });
      window.setTimeout(() => setCopiedShare(false), 1800);
    } catch {
      notify({
        tone: "warning",
        title: "Could not copy link",
        message: "Copy the product link from your browser address bar.",
        icon: "info"
      });
    }
  }

  async function handleCreateProductAlert(payload) {
    setAlertSaving(true);
    try {
      await storefrontExtrasApi.productAlerts.create(resolvedProductId, payload);
      notify({
        title: "Alert created",
        message: "We will notify you when this product is back in stock.",
        icon: "notifications_active"
      });
    } catch (requestError) {
      notify({
        tone: "warning",
        title: "Could not create alert",
        message: requestError?.normalized?.message || "Try again with a valid email address.",
        icon: "info"
      });
    } finally {
      setAlertSaving(false);
    }
  }

  return (
    <div className="product-detail-page">
      <Seo
        title={`${resolvedTitle} | Reesolmart`}
        description={seoDescription}
        canonicalPath={canonicalPath}
        image={seoImage}
        type="product"
        jsonLd={seoSchemas}
      />
      <BreadcrumbNav items={breadcrumbItems} />

      <section className="product-detail">
        <div className="product-detail__media-panel">
          <ProductImageGallery product={product} />
        </div>

        <div className="product-detail__body">
          <div className="product-detail__topline">
            <div>
              <h1>{resolvedTitle}</h1>
              <dl className="product-detail__identity product-detail__identity--inline">
                <div>
                  <dt>Brand</dt>
                  <dd>{brandLabel}</dd>
                </div>
                <div>
                  <dt>SKU</dt>
                  <dd>{resolvedSku}</dd>
                </div>
              </dl>
              <div className="product-detail__rating">
                <StarRating value={rating || 0} size={17} />
                <span>{rating ? rating.toFixed(1) : "0.0"}</span>
                <a href="#reviews" onClick={() => setActiveInfoTab("reviews")}>
                  ({reviewCount} review{reviewCount === 1 ? "" : "s"})
                </a>
                {!reviewCount ? <a href="#reviews" onClick={() => setActiveInfoTab("reviews")}>Be the first to review</a> : null}
              </div>
            </div>
          </div>

          <div className="product-price-block">
            <strong className="product-price">{price.label || "Price on request"}</strong>
            {price.previousLabel ? (
              <span>
                <del>{price.previousLabel}</del>
                {price.discountLabel ? <em>{price.discountLabel}</em> : null}
              </span>
            ) : price.sublabel ? <span>{price.sublabel}</span> : null}
          </div>

          <dl className="product-quick-facts" aria-label="Product facts">
            <div>
              <dt>Category</dt>
              <dd>{categoryLabel}</dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd><Badge tone={stock.tone}>{stock.label}</Badge></dd>
            </div>
          </dl>

          {quickSpecs.length ? (
            <section className="product-spec-summary" aria-label="Technical specification summary">
              <h2>Technical specification</h2>
              <div className="product-spec-summary__table-wrap">
                <table className="product-spec-summary__table">
                  <tbody>
                    {quickSpecs.map((spec) => (
                      <tr key={spec.code || spec.name}>
                        <th scope="row">{spec.name}</th>
                        <td>{formatSpecValue(spec.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {productHighlights.length ? (
            <section className="product-overview" aria-label="Product highlights">
              <div className="product-overview__head">
                <MaterialIcon name="checklist" size={18} />
                <h2>Product highlights</h2>
              </div>
              <ul>
                {productHighlights.map((item, index) => (
                  <li className={item.type === "number" ? "is-numbered" : ""} key={`${item.type}-${item.text}-${index}`}>
                    <span>{item.type === "number" ? index + 1 : ""}</span>
                    {item.text}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {productOptions.length ? (
            <div className="product-options">
              <h2>Choose options</h2>
              {optionError ? <p className="product-option-error">{optionError}</p> : null}
              {productOptions.map((option) => (
                <ProductOptionField
                  key={option.id || option.code}
                  option={option}
                  value={selectedOptions[option.id || option.code] || ""}
                  onChange={(value) => setSelectedOptions((current) => ({ ...current, [option.id || option.code]: value }))}
                />
              ))}
            </div>
          ) : null}

          <div className="product-purchase-panel">
            <div className="product-actions">
              <QuantityStepper
                value={boundedQuantity}
                max={maxQuantity}
                disabled={!canAddToCart || cartLoading}
                onChange={setQuantity}
              />
              <WishlistButton productId={resolvedProductId} productTitle={resolvedTitle} variant="detail" />
              {!stock.isAvailable ? (
                <Link className="secondary-button" to={`/quote?product=${resolvedProductId}`}>
                  <MaterialIcon name="request_quote" size={19} />
                  Request quote
                </Link>
              ) : null}
            </div>
            <button className={`primary-button${canAddToCart ? "" : " primary-button--muted"}`} type="button" disabled={cartLoading} onClick={() => void handleAddToCart()}>
              <MaterialIcon name="add_shopping_cart" size={19} />
              {cartLoading ? "Adding..." : canAddToCart ? "Add to cart" : "Sold out"}
            </button>
            <div className="product-secondary-actions">
              <button className="secondary-button callback-button" type="button" onClick={() => setCallbackOpen(true)}>
                <MaterialIcon name="phone_callback" size={19} />
                Call me back
              </button>
            </div>
          </div>

          {!stock.isAvailable ? (
            <ProductAlertForm
              defaultEmail={user?.email || ""}
              loading={alertSaving}
              onSubmit={handleCreateProductAlert}
            />
          ) : null}
        </div>

        <ProductSharePanel
          product={product}
          shareUrl={shareUrl}
          copied={copiedShare}
          onCopy={() => void handleCopyShare()}
          onNativeShare={() => void handleNativeShare()}
        />
      </section>

      <section className="product-info-tabs" aria-label="Product information">
        <div className="product-info-tabs__nav" role="tablist" aria-label="Product details">
          {[
            ["description", "Description"],
            ["reviews", "Reviews"]
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              id={`product-tab-${key}`}
              aria-selected={activeInfoTab === key}
              aria-controls={`product-panel-${key}`}
              className={activeInfoTab === key ? "is-active" : ""}
              onClick={() => setActiveInfoTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="product-info-tabs__body">
          <article
            id="product-panel-description"
            role="tabpanel"
            aria-labelledby="product-tab-description"
            hidden={activeInfoTab !== "description"}
          >
            {overviewText ? <p>{overviewText}</p> : <p>No product description has been added yet.</p>}
          </article>
          <article
            id="product-panel-reviews"
            role="tabpanel"
            aria-labelledby="product-tab-reviews"
            hidden={activeInfoTab !== "reviews"}
          >
            <div id="reviews">
              <ReviewList productId={resolvedProductId} />
            </div>
          </article>
        </div>
      </section>

      <RelatedProducts products={related} />
      {callbackOpen ? (
        <CallbackRequestModal
          productId={resolvedProductId}
          productTitle={resolvedTitle}
          user={user}
          onClose={() => setCallbackOpen(false)}
        />
      ) : null}
    </div>
  );
}

function CallbackRequestModal({ productId, productTitle: title, user, onClose }) {
  const notify = useUiStore((state) => state.notify);
  const [form, setForm] = useState({
    name: [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.name || "",
    phone_number: user?.phone_number || user?.phone || "",
    reason: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const result = await storefrontExtrasApi.callbackRequests.create({
        product_id: Number(productId),
        name: form.name.trim(),
        phone_number: form.phone_number.trim(),
        reason: form.reason.trim()
      });
      const deadline = result?.respond_by
        ? new Date(result.respond_by).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" })
        : "within three working hours";
      notify({
        title: "Callback requested",
        message: `Our team will call you by ${deadline}.`,
        icon: "phone_callback"
      });
      onClose();
    } catch (requestError) {
      const payload = requestError?.response?.data;
      const fieldError = payload && Object.values(payload).find((value) => Array.isArray(value));
      setError(fieldError?.[0] || requestError?.normalized?.message || "We could not submit your request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="callback-modal" role="dialog" aria-modal="true" aria-labelledby="callback-title" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !submitting) onClose();
    }}>
      <form className="callback-modal__panel" onSubmit={handleSubmit}>
        <button className="callback-modal__close" type="button" disabled={submitting} onClick={onClose} aria-label="Close">
          <MaterialIcon name="close" size={20} />
        </button>
        <span className="callback-modal__icon"><MaterialIcon name="phone_callback" size={26} /></span>
        <h2 id="callback-title">Call me back</h2>
        <p>Ask our team about <strong>{title}</strong>. We respond within three working hours, Monday-Friday, 7:00 AM-8:00 PM.</p>
        <Alert>{error}</Alert>
        <label>
          <span>Name</span>
          <input
            value={form.name}
            maxLength={160}
            autoComplete="name"
            required
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
          />
        </label>
        <label>
          <span>Phone number</span>
          <input
            type="tel"
            value={form.phone_number}
            maxLength={32}
            autoComplete="tel"
            placeholder="+254 700 000 000"
            required
            onChange={(event) => setForm((current) => ({ ...current, phone_number: event.target.value }))}
          />
        </label>
        <label>
          <span>Reason for request</span>
          <textarea
            value={form.reason}
            minLength={5}
            maxLength={2000}
            rows={4}
            placeholder="Tell us what you would like help with"
            required
            onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))}
          />
        </label>
        <div className="callback-modal__actions">
          <button className="primary-button" type="submit" disabled={submitting}>
            <MaterialIcon name="phone_callback" size={19} />
            {submitting ? "Sending..." : "Request callback"}
          </button>
          <button className="secondary-button" type="button" disabled={submitting} onClick={onClose}>Cancel</button>
        </div>
      </form>
    </div>
  );
}

function QuantityStepper({ value, max, disabled, onChange }) {
  const canDecrease = !disabled && value > 1;
  const canIncrease = !disabled && value < max;

  return (
    <div className="quantity-stepper" aria-label="Quantity">
      <button type="button" disabled={!canDecrease} onClick={() => onChange((current) => Math.max(1, current - 1))}>
        <MaterialIcon name="remove" size={18} />
      </button>
      <span>{value}</span>
      <button type="button" disabled={!canIncrease} onClick={() => onChange((current) => Math.min(max, current + 1))}>
        <MaterialIcon name="add" size={18} />
      </button>
    </div>
  );
}

function cleanOverview(value = "") {
  return String(value)
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeProductHighlights(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const source = item && typeof item === "object" ? item : { text: item };
      const text = cleanOverview(source.text || source.value || "");
      if (!text) return null;
      return {
        type: ["number", "numbered", "ordered"].includes(String(source.type || "").toLowerCase()) ? "number" : "bullet",
        text
      };
    })
    .filter(Boolean)
    .slice(0, 8);
}

function lastPathSegment(value = "") {
  return String(value || "")
    .split("/")
    .filter(Boolean)
    .pop() || "";
}

function buildProductSeoDescription(product, title, brand, category) {
  const overview = cleanOverview(product?.description || "");
  if (overview) return truncateText(overview, 155);
  return truncateText(`Buy ${title}${brand && brand !== "Not specified" ? ` by ${brand}` : ""} from Reesolmart. View price, stock availability, specifications, and delivery options${category ? ` for ${category}` : ""}.`, 155);
}

function buildProductSeoSchemas({ product, title, description, canonicalPath, image, price, stock, rating, reviewCount, brand, sku, breadcrumbs }) {
  const canonicalUrl = absoluteUrl(canonicalPath);
  const imageUrl = image ? absoluteUrl(image) : undefined;
  const breadcrumbItems = [
    { name: "Home", url: absoluteUrl("/") },
    { name: "Shop", url: absoluteUrl("/catalog") },
    ...breadcrumbs.map((category) => ({
      name: category.name || category.title || "Category",
      url: absoluteUrl(category.slug ? `/catalog/category/${category.slug}` : "/catalog")
    })),
    { name: title, url: canonicalUrl }
  ];

  const productSchema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: title,
    description,
    sku: sku || undefined,
    image: imageUrl ? [imageUrl] : undefined,
    brand: brand && brand !== "Not specified" ? { "@type": "Brand", name: brand } : undefined,
    category: productCategory(product, ""),
    url: canonicalUrl,
    offers: price?.isQuote
      ? undefined
      : {
          "@type": "Offer",
          url: canonicalUrl,
          priceCurrency: price.currency || product.currency || "KES",
          price: price.value,
          availability: stock.isAvailable ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
          itemCondition: "https://schema.org/NewCondition"
        },
    aggregateRating: reviewCount > 0 && rating > 0
      ? {
          "@type": "AggregateRating",
          ratingValue: Number(rating.toFixed(1)),
          reviewCount
        }
      : undefined
  };

  return [
    removeEmptySchemaValues(productSchema),
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: breadcrumbItems.map((item, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: item.name,
        item: item.url
      }))
    }
  ];
}

function removeEmptySchemaValues(value) {
  if (Array.isArray(value)) return value.map(removeEmptySchemaValues).filter((item) => item !== undefined);
  if (!value || typeof value !== "object") return value;

  return Object.fromEntries(
    Object.entries(value)
      .map(([key, item]) => [key, removeEmptySchemaValues(item)])
      .filter(([, item]) => item !== undefined && item !== "" && !(Array.isArray(item) && item.length === 0))
  );
}

function truncateText(value = "", maxLength = 155) {
  const clean = cleanOverview(value);
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength - 3).trimEnd()}...`;
}

function buildProductSpecs(product) {
  if (!product) return [];

  const specs = Array.isArray(product.specifications) ? [...product.specifications] : [];
  const existingNames = new Set(specs.map((spec) => String(spec.name || spec.code || "").toLowerCase()));

  function addSpec(name, value, code) {
    if (value === null || value === undefined || value === "") return;
    const key = String(name || code || "").toLowerCase();
    if (!key || existingNames.has(key)) return;
    existingNames.add(key);
    specs.push({ name, value, code: code || key });
  }

  addSpec("SKU", product.sku || product.upc || product.code, "sku");
  addSpec("Brand", productBrand(product), "brand");
  addSpec("Category", productCategory(product), "category");
  addSpec("Tags", Array.isArray(product.tags) ? product.tags.join(", ") : product.tags, "tags");
  addSpec("Weight", product.weight || product.weight_grams, "weight");
  addSpec("Dimensions", product.dimensions, "dimensions");

  return specs;
}

function buildQuickSpecs(specs = []) {
  const hidden = new Set(["sku", "brand", "category", "tags"]);
  return specs
    .filter((spec) => {
      const key = String(spec.code || spec.name || "").toLowerCase();
      return key && !hidden.has(key) && spec.value !== null && spec.value !== undefined && spec.value !== "";
    })
    .slice(0, 4);
}

function formatSpecValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join(", ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .filter(([, entryValue]) => entryValue !== null && entryValue !== undefined && entryValue !== "")
      .map(([key, entryValue]) => `${humanizeSpecKey(key)}: ${entryValue}`)
      .join(", ");
  }
  return String(value);
}

function humanizeSpecKey(key) {
  return String(key || "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function ProductSharePanel({ product, shareUrl, copied, onCopy, onNativeShare }) {
  const title = productTitle(product);
  const encodedUrl = encodeURIComponent(shareUrl);
  const encodedText = encodeURIComponent(`View ${title} on Reesolmart`);
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=12&data=${encodedUrl}`;
  const links = [
    {
      label: "WhatsApp",
      Icon: FaWhatsapp,
      className: "share-button--whatsapp",
      href: `https://wa.me/?text=${encodedText}%20${encodedUrl}`
    },
    {
      label: "Facebook",
      Icon: FaFacebookF,
      className: "share-button--facebook",
      href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`
    },
    {
      label: "X",
      Icon: FaXTwitter,
      className: "share-button--x",
      href: `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`
    },
    {
      label: "LinkedIn",
      Icon: FaLinkedinIn,
      className: "share-button--linkedin",
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`
    }
  ];

  return (
    <section className="product-share-panel" aria-label="Share this product">
      <div className="product-share-panel__head">
        <span>
          <MaterialIcon name="qr_code_2" size={22} />
        </span>
        <div>
          <h2>Scan to share</h2>
        </div>
      </div>

      <div className="product-share-panel__body">
        <a className="product-share-qr" href={shareUrl} aria-label={`Open share link for ${title}`}>
          <img src={qrUrl} alt={`QR code for ${title}`} loading="lazy" />
        </a>
        <div className="product-share-actions">
          <button className="secondary-button product-share-native" type="button" onClick={onNativeShare}>
            <MaterialIcon name="ios_share" size={18} />
            Share product
          </button>
          <button className="secondary-button product-share-native" type="button" onClick={onCopy}>
            <MaterialIcon name={copied ? "check" : "content_copy"} size={18} />
            {copied ? "Copied" : "Copy link"}
          </button>
          <div className="social-share-list">
            {links.map((link) => (
              <a
                key={link.label}
                className={`social-share-button ${link.className}`}
                href={link.href}
                target="_blank"
                rel="noreferrer"
                aria-label={`Share on ${link.label}`}
                title={link.label}
              >
                <link.Icon aria-hidden="true" />
                <span className="visually-hidden">{link.label}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ProductOptionField({ option, value, onChange }) {
  const choices = option.choices || option.values || option.options || [];
  const label = option.name || option.label || option.code || "Option";
  const required = Boolean(option.required);
  const helpText = option.help_text || option.helpText || "";

  return (
    <label className="product-option-field">
      <span>
        {label}
        {required ? " *" : ""}
      </span>
      {helpText ? <small>{helpText}</small> : null}
      {choices.length ? (
        <select value={value} required={required} onChange={(event) => onChange(event.target.value)}>
          <option value="">Select {label.toLowerCase()}</option>
          {choices.map((choice) => {
            const choiceValue = choice.value ?? choice.id ?? choice;
            const choiceLabel = choice.label ?? choice.name ?? choice.value ?? choice;
            return (
              <option key={choiceValue} value={choiceValue}>
                {choiceLabel}
              </option>
            );
          })}
        </select>
      ) : (
        <input value={value} required={required} placeholder={`Enter ${label.toLowerCase()}`} onChange={(event) => onChange(event.target.value)} />
      )}
    </label>
  );
}
