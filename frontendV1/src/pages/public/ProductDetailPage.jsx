import { useEffect } from "react";
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
import { useWishlistStore } from "../../store/wishlist.store";
import { productPrice, stockTone } from "../../utils/productDisplay";

export default function ProductDetailPage() {
  const { productId } = useParams();
  const { product, related, loading, error } = useProductDetail(productId);
  const addItem = useCartStore((state) => state.addItem);
  const cartLoading = useCartStore((state) => state.loading);
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);

  useEffect(() => {
    if (user && product?.id) void loadStatus([product.id]);
  }, [loadStatus, product?.id, user]);

  if (loading) return <Spinner label="Loading product" />;
  if (error) return <Alert>{error}</Alert>;
  if (!product) return <Alert tone="warning">Product not found.</Alert>;

  const price = productPrice(product);
  const stock = stockTone(product);
  const categoryLabel = product.categories?.[0]?.name || "Uncategorized";
  const reviewCount = Number(product.review_count || product.reviews_count || 0);
  const rating = Number(product.rating || product.average_review_score || 0);

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
          </dl>
          <p>{product.description || "No product description has been added yet."}</p>
          <div className="product-actions">
            <button className="primary-button" type="button" disabled={cartLoading} onClick={() => void addItem(product.id)}>
              <MaterialIcon name="add_shopping_cart" size={19} />
              {cartLoading ? "Adding..." : "Add to cart"}
            </button>
            <WishlistButton productId={product.id} productTitle={product.title} variant="detail" />
            <Link className="secondary-button" to={`/quote?product=${product.id}`}>
              <MaterialIcon name="request_quote" size={19} />
              Request quote
            </Link>
          </div>
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
