import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ProductImageGallery from "../../components/catalog/ProductImageGallery.jsx";
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
import { productPrice, stockTone } from "../../utils/productDisplay";

export default function ProductDetailPage() {
  const { productId } = useParams();
  const { product, related, loading, error } = useProductDetail(productId);
  const addItem = useCartStore((state) => state.addItem);
  const cartLoading = useCartStore((state) => state.loading);
  const notify = useUiStore((state) => state.notify);
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [optionError, setOptionError] = useState("");
  const [copiedShare, setCopiedShare] = useState(false);
  const productOptions = useMemo(() => product?.options || product?.product_options || [], [product]);
  const missingRequiredOptions = useMemo(
    () => productOptions.filter((option) => option.required && !selectedOptions[option.id || option.code]),
    [productOptions, selectedOptions]
  );
  const shareUrl = useMemo(() => {
    const path = `/products/${productId}`;
    if (typeof window === "undefined") return path;
    return new URL(path, window.location.origin).toString();
  }, [productId]);

  useEffect(() => {
    if (user && product?.id) void loadStatus([product.id]);
  }, [loadStatus, product?.id, user]);

  if (loading) return <Spinner label="Loading product" />;
  if (error) return <Alert>{error}</Alert>;
  if (!product) return <Alert tone="warning">Product not found.</Alert>;

  const price = productPrice(product);
  const stock = stockTone(product);
  const canAddToCart = stock.isAvailable && !price.isQuote;
  const categoryLabel = product.categories?.[0]?.name || "Uncategorized";
  const reviewCount = Number(product.review_count || product.reviews_count || 0);
  const rating = Number(product.rating || product.average_review_score || 0);

  async function handleAddToCart() {
    if (!stock.isAvailable) {
      notify({
        tone: "warning",
        title: "Sold out",
        message: `${product.title} is out of stock right now.`
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
      await addItem(product.id, 1, options);
    } catch {
      // Global notification state already shows the failed action.
    }
  }

  async function handleNativeShare() {
    const payload = {
      title: product.title,
      text: `View ${product.title} on Vortexus`,
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

  return (
    <>
      <Link className="back-link" to="/catalog">
        &lt; Back to catalog
      </Link>
      <section className="product-detail">
        <ProductImageGallery product={product} />
        <div className="product-detail__body">
          <div className="product-detail__meta">
            <Badge tone={stock.tone}>{stock.label}</Badge>
            <span>{categoryLabel}</span>
          </div>
          <h1>{product.title}</h1>
          {reviewCount > 0 ? (
            <div className="product-detail__rating">
              <StarRating value={rating} size={16} />
              <span>{rating.toFixed(1)}</span>
              <a href="#reviews">{reviewCount} review{reviewCount === 1 ? "" : "s"}</a>
            </div>
          ) : null}
          <div className="product-price-block">
            <strong className="product-price">{price.label || "Price on request"}</strong>
            {price.sublabel ? <span>{price.sublabel}</span> : null}
          </div>
          <dl className="product-quick-facts">
            <div>
              <dt>SKU</dt>
              <dd>{product.sku || "Pending"}</dd>
            </div>
            <div>
              <dt>Category</dt>
              <dd>{categoryLabel}</dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd>{stock.label}</dd>
            </div>
          </dl>
          <p>{product.description || "No product description has been added yet."}</p>
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
            <button className={`primary-button${canAddToCart ? "" : " primary-button--muted"}`} type="button" disabled={cartLoading} onClick={() => void handleAddToCart()}>
              <MaterialIcon name="add_shopping_cart" size={19} />
              {cartLoading ? "Adding..." : canAddToCart ? "Add to cart" : "Sold out"}
            </button>
            <WishlistButton productId={product.id} productTitle={product.title} variant="detail" />
            <Link className="secondary-button" to={`/quote?product=${product.id}`}>
              <MaterialIcon name="request_quote" size={19} />
              Request quote
            </Link>
          </div>
          <ProductSharePanel
            product={product}
            shareUrl={shareUrl}
            copied={copiedShare}
            onCopy={() => void handleCopyShare()}
            onNativeShare={() => void handleNativeShare()}
          />
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading">
          <h2>Technical specifications</h2>
        </div>
        <ProductSpecifications specifications={product.specifications || []} />
      </section>

      <div id="reviews">
        <ReviewList productId={product.id} />
      </div>

      <RelatedProducts products={related} />
    </>
  );
}

function ProductSharePanel({ product, shareUrl, copied, onCopy, onNativeShare }) {
  const encodedUrl = encodeURIComponent(shareUrl);
  const encodedText = encodeURIComponent(`View ${product.title} on Vortexus`);
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=12&data=${encodedUrl}`;
  const links = [
    {
      label: "WhatsApp",
      short: "WA",
      className: "share-button--whatsapp",
      href: `https://wa.me/?text=${encodedText}%20${encodedUrl}`
    },
    {
      label: "Facebook",
      short: "f",
      className: "share-button--facebook",
      href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`
    },
    {
      label: "X",
      short: "X",
      className: "share-button--x",
      href: `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`
    },
    {
      label: "LinkedIn",
      short: "in",
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
        <a className="product-share-qr" href={shareUrl} aria-label={`Open share link for ${product.title}`}>
          <img src={qrUrl} alt={`QR code for ${product.title}`} loading="lazy" />
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
                {link.short}
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
