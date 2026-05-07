import ProductGrid from "./ProductGrid.jsx";

export default function RelatedProducts({ products = [] }) {
  return (
    <section className="content-section">
      <div className="section-heading">
        <h2>Related products</h2>
      </div>
      <ProductGrid products={products} emptyTitle="No related products yet" />
    </section>
  );
}
