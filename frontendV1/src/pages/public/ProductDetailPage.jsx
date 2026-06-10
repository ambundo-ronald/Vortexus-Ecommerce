import { useEffect, useMemo, useState } from "react";
import { FaFacebookF, FaLinkedinIn, FaWhatsapp } from "react-icons/fa";
import { FaXTwitter } from "react-icons/fa6";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import ProductImageGallery from "../../components/catalog/ProductImageGallery.jsx";
import ProductAlertForm from "../../components/catalog/ProductAlertForm.jsx";
import ProductSpecifications from "../../components/catalog/ProductSpecifications.jsx";
import RelatedProducts from "../../components/catalog/RelatedProducts.jsx";
import ReviewList from "../../components/reviews/ReviewList.jsx";
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
import { trackStorefrontEvent } from "../../utils/analytics";
import {
  productBrand,
  productCategory,
  productId as resolveProductId,
  productPrice,
  productRating,
  productSku,
  productTitle,
  stockTone
} from "../../utils/productDisplay";
import "./ProductDetailPage.css";

export default function ProductDetailPage() {
  const { productId: routeProductId } = useParams();
  const { product, related, loading, error } = useProductDetail(routeProductId);
  const addItem = useCartStore((state) => state.addItem);
  const cartLoading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [optionError, setOptionError] = useState("");
  const [copiedShare, setCopiedShare] = useState(false);
  const [alertSaving, setAlertSaving] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const productOptions = useMemo(() => product?.options || product?.product_options || [], [product]);
  const missingRequiredOptions = useMemo(
    () => productOptions.filter((option) => option.required && !selectedOptions[option.id || option.code]),
    [productOptions, selectedOptions]
  );
  const category = useMemo(() => product?.categories?.[0] || null, [product]);
  const categoryLabel = productCategory(product || {}, "Uncategorized");
  const categoryHref = category ? `/catalog/category/${category.slug || category.id}` : "/catalog";
  const detailSpecs = useMemo(() => buildProductSpecs(product), [product]);
  const overviewText = useMemo(() => cleanOverview(product?.description) || "No product description has been added yet.", [product?.description]);
  const resolvedProductId = resolveProductId(product || {}) || routeProductId;
  const resolvedTitle = productTitle(product || {});
  const resolvedSku = productSku(product || {}, "Pending");
  const shareUrl = useMemo(() => {
    const path = `/products/${resolvedProductId || routeProductId}`;
    if (typeof window === "undefined") return path;
    return new URL(path, window.location.origin).toString();
  }, [resolvedProductId, routeProductId]);

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
      product_id: resolvedProductId,
      product_title: resolvedTitle,
      path: `/products/${resolvedProductId}`
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
      await addItem(resolvedProductId, boundedQuantity, options);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  async function handleNativeShare() {
    const payload = {
      title: resolvedTitle,
      text: `View ${resolvedTitle} on Vortexus`,
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
      <nav className="product-breadcrumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <MaterialIcon name="chevron_right" size={16} />
        <Link to="/catalog">Shop</Link>
        <MaterialIcon name="chevron_right" size={16} />
        <Link to={categoryHref}>{categoryLabel}</Link>
        <MaterialIcon name="chevron_right" size={16} />
        <span>{resolvedTitle}</span>
      </nav>

      <section className="product-detail">
        <div className="product-detail__media-panel">
          <ProductImageGallery product={product} />
          <ProductTrustBar />
        </div>

        <div className="product-detail__body">
          <div className="product-detail__topline">
            <div>
              <h1>{resolvedTitle}</h1>
              <div className="product-detail__rating">
                <StarRating value={rating || 0} size={17} />
                <span>{rating ? rating.toFixed(1) : "0.0"}</span>
                <a href="#reviews">
                  ({reviewCount} review{reviewCount === 1 ? "" : "s"})
                </a>
                {!reviewCount ? <a href="#reviews">Be the first to review</a> : null}
              </div>
            </div>
            <dl className="product-detail__identity">
              <div>
                <dt>SKU</dt>
                <dd>{resolvedSku}</dd>
              </div>
              <div>
                <dt>Brand</dt>
                <dd>{brandLabel}</dd>
              </div>
            </dl>
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

          <dl className="product-quick-facts">
            <div>
              <dt>Category</dt>
              <dd>{categoryLabel}</dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd><Badge tone={stock.tone}>{stock.label}</Badge></dd>
            </div>
          </dl>

          <section className="product-overview" aria-label="Quick overview">
            <h2>Quick overview</h2>
            <p>{overviewText}</p>
          </section>

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

          <div className="product-actions">
            <QuantityStepper
              value={boundedQuantity}
              max={maxQuantity}
              disabled={!canAddToCart || cartLoading}
              onChange={setQuantity}
            />
            <button className={`primary-button${canAddToCart ? "" : " primary-button--muted"}`} type="button" disabled={cartLoading} onClick={() => void handleAddToCart()}>
              <MaterialIcon name="add_shopping_cart" size={19} />
              {cartLoading ? "Adding..." : canAddToCart ? "Add to cart" : "Sold out"}
            </button>
            <WishlistButton productId={resolvedProductId} productTitle={resolvedTitle} variant="detail" />
            <Link className="secondary-button" to={`/quote?product=${resolvedProductId}`}>
              <MaterialIcon name="request_quote" size={19} />
              Request quote
            </Link>
          </div>

          {!stock.isAvailable ? (
            <ProductAlertForm
              defaultEmail={user?.email || ""}
              loading={alertSaving}
              onSubmit={handleCreateProductAlert}
            />
          ) : null}
        </div>
      </section>

      <ProductSharePanel
        product={product}
        shareUrl={shareUrl}
        copied={copiedShare}
        onCopy={() => void handleCopyShare()}
        onNativeShare={() => void handleNativeShare()}
      />

      <section className="product-info-grid">
        <article className="product-info-card">
          <h2>Why choose this product?</h2>
          <ul className="product-benefit-list">
            <li><MaterialIcon name="check_circle" size={18} filled /> High performance and reliable operation</li>
            <li><MaterialIcon name="check_circle" size={18} filled /> Built with durable project-ready materials</li>
            <li><MaterialIcon name="check_circle" size={18} filled /> Easy to install, maintain, and reorder</li>
            <li><MaterialIcon name="check_circle" size={18} filled /> Suitable for industrial and commercial use</li>
          </ul>
        </article>

        <article className="product-info-card">
          <h2>Technical specifications</h2>
          <ProductSpecifications specifications={detailSpecs} />
        </article>
      </section>

      <div id="reviews">
        <ReviewList productId={resolvedProductId} />
      </div>

      <RelatedProducts products={related} />
    </div>
  );
}

function ProductTrustBar() {
  const items = [
    { icon: "verified_user", title: "Premium quality" },
    { icon: "workspace_premium", title: "Warranty ready" },
    { icon: "inventory_2", title: "Secure packaging" }
  ];

  return (
    <div className="product-trust-bar" aria-label="Product trust signals">
      {items.map((item) => (
        <span key={item.title}>
          <MaterialIcon name={item.icon} size={19} />
          {item.title}
        </span>
      ))}
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

function ProductSharePanel({ product, shareUrl, copied, onCopy, onNativeShare }) {
  const title = productTitle(product);
  const encodedUrl = encodeURIComponent(shareUrl);
  const encodedText = encodeURIComponent(`View ${title} on Vortexus`);
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
          <p>Open this product quickly on another phone.</p>
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
