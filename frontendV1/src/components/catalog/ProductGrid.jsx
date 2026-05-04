import { useEffect } from "react";

import EmptyState from "../ui/EmptyState.jsx";
import ProductCard from "./ProductCard.jsx";
import ProductSkeletonGrid from "./ProductSkeletonGrid.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useWishlistStore } from "../../store/wishlist.store";

export default function ProductGrid({ products = [], emptyTitle = "No products found", loading = false, skeletonCount = 8 }) {
  const { user } = useAuth();
  const loadStatus = useWishlistStore((state) => state.loadStatus);
  const productIds = products.map((product) => product.id).filter(Boolean).join(",");

  useEffect(() => {
    if (user && productIds) void loadStatus(productIds.split(","));
  }, [loadStatus, productIds, user]);

  if (loading) {
    return <ProductSkeletonGrid count={skeletonCount} />;
  }

  if (!products.length) {
    return <EmptyState title={emptyTitle} message="Try another category, search term, or filter." />;
  }

  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
