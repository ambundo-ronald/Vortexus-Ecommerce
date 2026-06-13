import { useEffect, useMemo, useState } from "react";

import { catalogApi } from "../../api/catalog.api";
import { supplierApi } from "../../api/supplier.api";
import SupplierProductTable from "../../components/supplier/SupplierProductTable.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";

const initialForm = {
  id: null,
  upc: "",
  title: "",
  description: "",
  category_id: "",
  partner_sku: "",
  price: "",
  currency: "KES",
  num_in_stock: "0",
  brand: ""
};

export default function SupplierProductsPage() {
  const notify = useUiStore((state) => state.notify);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [imageFiles, setImageFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [productPayload, categoryPayload] = await Promise.all([
          supplierApi.products({ page_size: 60 }),
          catalogApi.categories()
        ]);
        if (!mounted) return;
        setProducts(productPayload.results || []);
        setCategories(flattenCategories(categoryPayload.results || categoryPayload.categories || []));
      } catch (err) {
        if (mounted) setError(err.normalized?.message || err.message || "Could not load supplier products.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const selectedProduct = useMemo(() => products.find((item) => item.id === form.id), [form.id, products]);

  async function reloadProducts() {
    const payload = await supplierApi.products({ page_size: 60 });
    setProducts(payload.results || []);
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function editProduct(product) {
    setForm({
      id: product.id,
      upc: product.upc || product.sku || "",
      title: product.title || "",
      description: product.description || "",
      category_id: product.categories?.[0]?.id ? String(product.categories[0].id) : "",
      partner_sku: product.offer?.partner_sku || product.upc || "",
      price: product.offer?.price ?? "",
      currency: product.offer?.currency || product.currency || "KES",
      num_in_stock: String(product.offer?.num_in_stock ?? 0),
      brand: product.brand || ""
    });
    setFormError("");
  }

  function resetForm() {
    setForm(initialForm);
    setImageFiles([]);
    setFormError("");
  }

  async function submitProduct(event) {
    event.preventDefault();
    setFormError("");
    if (!form.upc.trim() || !form.title.trim()) {
      setFormError("SKU and product title are required.");
      return;
    }

    const payload = {
      upc: form.upc.trim(),
      title: form.title.trim(),
      description: form.description.trim(),
      partner_sku: form.partner_sku.trim() || form.upc.trim(),
      currency: form.currency || "KES",
      num_in_stock: Number(form.num_in_stock || 0),
      attributes: {
        brand: form.brand.trim()
      }
    };
    if (form.price !== "") payload.price = form.price;
    if (form.category_id) payload.category_ids = [Number(form.category_id)];

    setSaving(true);
    try {
      let result;
      if (form.id) {
        result = await supplierApi.updateProduct(form.id, payload);
        notify({ title: "Product resubmitted", message: "Your changes are pending review.", icon: "rate_review" });
      } else {
        result = await supplierApi.createProduct(payload);
        notify({ title: "Product submitted", message: "It is pending approval before going live.", icon: "inventory_2" });
      }
      const productId = result?.product?.id || form.id;
      if (productId && imageFiles.length) {
        await uploadImages(productId);
        notify({ title: "Images uploaded", message: `${imageFiles.length} product image${imageFiles.length === 1 ? "" : "s"} attached.`, icon: "photo_library" });
      }
      resetForm();
      await reloadProducts();
    } catch (err) {
      setFormError(fieldMessage(err) || err.normalized?.message || err.message || "Could not save product.");
    } finally {
      setSaving(false);
    }
  }

  async function uploadImages(productId) {
    for (const file of imageFiles) {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("alt", form.title.trim() || file.name);
      await supplierApi.uploadProductImage(productId, formData);
    }
  }

  if (loading) return <Spinner label="Loading supplier products" />;

  return (
    <section className="account-page supplier-page">
      <div className="account-section-title">
        <div>
          <p className="eyebrow">Supplier Portal</p>
          <h1>Products</h1>
          <p>Upload products and track review status before they appear on the storefront.</p>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <div className="supplier-products-layout">
        <div className="surface-panel supplier-product-list">
          <div className="supplier-panel-heading">
            <div>
              <h2>Submitted products</h2>
              <p>{products.length} products in your supplier catalogue</p>
            </div>
            <button className="secondary-button" type="button" onClick={() => void reloadProducts()}>
              <MaterialIcon name="refresh" size={18} />
              Refresh
            </button>
          </div>
          <SupplierProductTable products={products} onEdit={editProduct} />
        </div>

        <form className="surface-panel supplier-product-form" onSubmit={submitProduct}>
          <div className="supplier-panel-heading">
            <div>
              <h2>{form.id ? "Edit product" : "Add product"}</h2>
              <p>{form.id ? "Editing resubmits the product for review." : "New products stay pending until staff approves them."}</p>
            </div>
            {form.id ? (
              <button className="secondary-button" type="button" onClick={resetForm}>
                Clear
              </button>
            ) : null}
          </div>

          {selectedProduct?.moderation?.status ? (
            <Alert tone={selectedProduct.moderation.status === "approved" ? "success" : "info"}>
              Current status: {formatStatus(selectedProduct.moderation.status)}
            </Alert>
          ) : null}
          {formError ? <Alert>{formError}</Alert> : null}

          <label>
            <span>SKU</span>
            <input value={form.upc} onChange={(event) => updateField("upc", event.target.value)} disabled={saving || Boolean(form.id)} />
          </label>
          <label>
            <span>Product title</span>
            <input value={form.title} onChange={(event) => updateField("title", event.target.value)} disabled={saving} />
          </label>
          <label>
            <span>Brand</span>
            <input value={form.brand} onChange={(event) => updateField("brand", event.target.value)} disabled={saving} />
          </label>
          <label>
            <span>Category</span>
            <select value={form.category_id} onChange={(event) => updateField("category_id", event.target.value)} disabled={saving}>
              <option value="">Select category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Description</span>
            <textarea rows={5} value={form.description} onChange={(event) => updateField("description", event.target.value)} disabled={saving} />
          </label>
          <label>
            <span>Product photos</span>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => setImageFiles(Array.from(event.target.files || []))}
              disabled={saving}
            />
            {imageFiles.length ? <small>{imageFiles.length} image{imageFiles.length === 1 ? "" : "s"} selected</small> : null}
          </label>
          <div className="supplier-form-grid">
            <label>
              <span>Price</span>
              <input type="number" min="0" step="0.01" value={form.price} onChange={(event) => updateField("price", event.target.value)} disabled={saving} />
            </label>
            <label>
              <span>Currency</span>
              <select value={form.currency} onChange={(event) => updateField("currency", event.target.value)} disabled={saving}>
                <option value="KES">KES</option>
                <option value="UGX">UGX</option>
                <option value="TZS">TZS</option>
                <option value="USD">USD</option>
              </select>
            </label>
            <label>
              <span>Stock</span>
              <input type="number" min="0" step="1" value={form.num_in_stock} onChange={(event) => updateField("num_in_stock", event.target.value)} disabled={saving} />
            </label>
          </div>

          <button className="primary-button" type="submit" disabled={saving}>
            <MaterialIcon name={saving ? "hourglass_top" : "send"} size={18} />
            {saving ? "Submitting..." : form.id ? "Resubmit for review" : "Submit for review"}
          </button>
        </form>
      </div>
    </section>
  );
}

function flattenCategories(categories = [], depth = 0) {
  return categories.flatMap((category) => {
    const current = {
      id: category.id,
      label: `${"\u00a0".repeat(depth * 2)}${category.name}`
    };
    return [current, ...flattenCategories(category.children || [], depth + 1)];
  });
}

function formatStatus(status = "") {
  return status.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function fieldMessage(error) {
  const data = error?.response?.data || error?.normalized?.data;
  if (!data || typeof data !== "object") return "";
  const entries = Object.entries(data);
  if (!entries.length) return "";
  const [field, value] = entries[0];
  const text = Array.isArray(value) ? value.join(" ") : String(value);
  return `${field.replaceAll("_", " ")}: ${text}`;
}
