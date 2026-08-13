import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ProductCarousel from "../../components/catalog/ProductCarousel.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { personalShopperApi } from "../../api/personalShopper.api";
import { useCartStore } from "../../store/cart.store";
import { productImageUrl } from "../../utils/productImages";
import { productInitials, productPrice, productSku, productTitle, productUrl, stockTone } from "../../utils/productDisplay";
import "./HubPage.css";
import "./HubDiscount.css";

export default function HubPage() {
  const { shareToken } = useParams();
  const addItem = useCartStore((state) => state.addItem);
  const applyVoucher = useCartStore((state) => state.applyVoucher);
  const cartLoading = useCartStore((state) => state.loading);
  const [shopperList, setShopperList] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addingAll, setAddingAll] = useState(false);
  const [addedIds, setAddedIds] = useState([]);
  const [discountApplied, setDiscountApplied] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    personalShopperApi.hub(shareToken)
      .then((payload) => {
        if (!active) return;
        setShopperList(payload.shopper_list);
        setRecommendations(payload.recommendations || []);
      })
      .catch((err) => active && setError(err.normalized?.message || err.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [shareToken]);

  const availableItems = useMemo(() => (shopperList?.items || []).filter((item) => {
    const stock = stockTone(item.product);
    return stock.isAvailable && !productPrice(item.product).isQuote;
  }), [shopperList]);

  async function addOne(item) {
    await addItem(item.product.id, item.quantity, [], { source: "personal_shopper", shopper_list_id: shopperList.id });
    setAddedIds((current) => [...new Set([...current, item.id])]);
    await personalShopperApi.markAddedToCart(shareToken);
  }

  async function addAll() {
    setAddingAll(true);
    const successful = [];
    for (const item of availableItems) {
      try {
        await addItem(item.product.id, item.quantity, [], { source: "personal_shopper", shopper_list_id: shopperList.id });
        successful.push(item.id);
      } catch {
        // The cart store reports per-item stock and pricing failures.
      }
    }
    if (successful.length) {
      setAddedIds((current) => [...new Set([...current, ...successful])]);
      await personalShopperApi.markAddedToCart(shareToken);
      if (shopperList.discount?.code) {
        try {
          await applyVoucher(shopperList.discount.code);
          setDiscountApplied(true);
        } catch {
          // The cart store shows the voucher error and it can be retried below.
        }
      }
    }
    setAddingAll(false);
  }

  async function applyDiscount() {
    await applyVoucher(shopperList.discount.code);
    setDiscountApplied(true);
  }

  if (loading) return <div className="hub-page"><Spinner label="Opening your personal shopper list" /></div>;
  if (error) return <div className="hub-page"><Alert>{error}</Alert><Link className="secondary-button" to="/account">Back to account</Link></div>;
  if (!shopperList) return null;

  return (
    <main className="hub-page">
      <header className="hub-hero">
        <div>
          <span className="hub-eyebrow"><MaterialIcon name="shopping_bag" size={18} /> Your Personal Shopper Hub</span>
          <h1>{shopperList.title}</h1>
          <p>{shopperList.note || "A product list selected especially for you by our team."}</p>
          <div className="hub-meta">
            <span>Prepared by {shopperList.created_by.name}</span>
            {shopperList.expires_at ? <span>Available until {new Date(shopperList.expires_at).toLocaleDateString()}</span> : null}
          </div>
        </div>
        <button className="primary-button hub-add-all" type="button" disabled={addingAll || cartLoading || !availableItems.length} onClick={() => void addAll()}>
          <MaterialIcon name="add_shopping_cart" size={19} />
          {addingAll ? "Adding items…" : `Add all available (${availableItems.length})`}
        </button>
      </header>

      {Number(shopperList.discount?.percentage || 0) > 0 ? (
        <section className="hub-discount" aria-label="Personal shopper discount">
          <span className="hub-discount__icon"><MaterialIcon name="sell" size={24} /></span>
          <div>
            <strong>{shopperList.discount.percentage}% off your curated items</strong>
            <p>Use your private code <code>{shopperList.discount.code}</code>. It applies only to products in this list.</p>
          </div>
          <button className="secondary-button" type="button" disabled={cartLoading || discountApplied} onClick={() => void applyDiscount()}>
            <MaterialIcon name={discountApplied ? "check_circle" : "sell"} size={17} /> {discountApplied ? "Discount applied" : "Apply code"}
          </button>
        </section>
      ) : null}

      <section className="hub-list" aria-labelledby="hub-list-title">
        <div className="hub-list__heading"><h2 id="hub-list-title">Selected for you</h2><span>{shopperList.items.length} products</span></div>
        <div className="hub-table-head"><span>Product</span><span>Price</span><span>Qty</span><span></span></div>
        {shopperList.items.map((item) => <HubItem key={item.id} item={item} added={addedIds.includes(item.id)} disabled={cartLoading || addingAll} onAdd={() => addOne(item)} />)}
      </section>

      {addedIds.length ? <div className="hub-cart-callout"><span>{addedIds.length} selection{addedIds.length === 1 ? " is" : "s are"} now in your cart.{discountApplied ? " Your discount is applied." : ""}</span><Link className="primary-button" to="/checkout/cart">View cart</Link></div> : null}

      {recommendations.length ? (
        <section className="hub-recommendations">
          <div className="section-heading"><div><span className="hub-eyebrow">Complete your setup</span><h2>You may also need</h2></div></div>
          <ProductCarousel products={recommendations} />
        </section>
      ) : null}
    </main>
  );
}

function HubItem({ item, added, disabled, onAdd }) {
  const product = item.product || {};
  const title = productTitle(product);
  const price = productPrice(product);
  const stock = stockTone(product);
  const image = productImageUrl(product);
  const canAdd = stock.isAvailable && !price.isQuote;
  const productPath = product.id ? productUrl(product) : "/catalog";
  return (
    <article className="hub-item">
      <Link className="hub-item__product" to={productPath}>
        <span className="hub-item__media">{image ? <img src={image} alt={title} /> : productInitials(title)}</span>
        <span><strong>{title}</strong><small>SKU: {productSku(product, "—")}</small>{item.note ? <em>{item.note}</em> : null}</span>
      </Link>
      <strong className="hub-item__price">{price.label || "Quote on request"}</strong>
      <span className="hub-item__quantity">× {item.quantity}</span>
      <div className="hub-item__action">
        <span className={`hub-stock ${stock.isAvailable ? "available" : "unavailable"}`}>{stock.label}</span>
        <button className="secondary-button" type="button" disabled={disabled || !canAdd || added} onClick={() => void onAdd()}>
          <MaterialIcon name={added ? "check_circle" : "add_shopping_cart"} size={17} /> {added ? "Added" : "Add"}
        </button>
      </div>
    </article>
  );
}
