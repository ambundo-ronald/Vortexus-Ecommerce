import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { searchApi } from "../../api/search.api";
import { useCategories } from "../../hooks/useCategories";
import { trackStorefrontEvent } from "../../utils/analytics";

export default function SearchBar({ initialValue = "", compact = false }) {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const formRef = useRef(null);
  const fileRef = useRef(null);
  const navigate = useNavigate();
  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories();

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  useEffect(() => {
    function closeMenusOnOutsideClick(event) {
      if (!formRef.current?.contains(event.target)) {
        setCategoriesOpen(false);
        setSuggestionsOpen(false);
      }
    }

    document.addEventListener("mousedown", closeMenusOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeMenusOnOutsideClick);
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      return undefined;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const payload = await searchApi.suggestions({ q: trimmed, limit: 6 });
        if (!cancelled) {
          setSuggestions(payload.results || []);
          setSuggestionsOpen(true);
        }
      } catch {
        if (!cancelled) setSuggestions([]);
      }
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  function submitSearch(event) {
    event.preventDefault();
    const trimmed = query.trim();
    setSuggestionsOpen(false);
    trackStorefrontEvent("search_submitted", { search: trimmed, path: window.location.pathname });
    navigate(trimmed ? `/search?q=${encodeURIComponent(trimmed)}` : "/search");
  }

  function openSuggestion(title) {
    setQuery(title);
    setSuggestionsOpen(false);
    navigate(`/search?q=${encodeURIComponent(title)}`);
  }

  function openCategory(category) {
    setCategoriesOpen(false);
    setSuggestionsOpen(false);
    if (!category?.slug) {
      navigate("/catalog");
      return;
    }
    navigate(`/catalog/category/${category.slug}`);
  }

  async function handleImageChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    trackStorefrontEvent("image_search_submitted", { source: "search_bar", path: window.location.pathname });
    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("top_k", "24");
      const payload = await searchApi.image(formData);
      navigate("/search?image=1", { state: { imagePayload: payload, imageName: file.name } });
    } catch (error) {
      navigate("/search?image=1", { state: { imageError: error.normalized?.message || error.message || "Image search failed." } });
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  return (
    <form ref={formRef} className={compact ? "search-form search-form--compact" : "search-form"} onSubmit={submitSearch} autoComplete="off">
      <button className="search-form__camera" type="button" disabled={uploading} onClick={() => fileRef.current?.click()} aria-label="Image search">
        <MaterialIcon name={uploading ? "hourglass_top" : "photo_camera"} size={24} />
      </button>
      <input ref={fileRef} className="visually-hidden" type="file" accept="image/*" onChange={handleImageChange} />
      <input
        type="search"
        value={query}
        onBlur={() => window.setTimeout(() => setSuggestionsOpen(false), 140)}
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => suggestions.length && setSuggestionsOpen(true)}
        placeholder="Search pumps, tanks, controllers..."
        aria-label="Search products"
      />
      <button
        className="search-form__category-toggle"
        type="button"
        aria-label="Browse categories"
        aria-expanded={categoriesOpen}
        onClick={() => {
          setSuggestionsOpen(false);
          setCategoriesOpen((current) => !current);
        }}
      >
        <MaterialIcon name="category" size={20} />
        <span>Categories</span>
        <MaterialIcon name="keyboard_arrow_down" size={18} />
      </button>
      <button type="submit" aria-label="Search">
        <MaterialIcon name="search" size={28} />
      </button>
      {categoriesOpen ? (
        <div className="search-form__category-menu" role="menu" aria-label="Product categories">
          <button type="button" onClick={() => openCategory(null)} role="menuitem">
            <MaterialIcon name="apps" size={18} />
            <span>All categories</span>
          </button>
          {categories.map((category) => (
            <button type="button" key={category.id || category.slug || category.name} onClick={() => openCategory(category)} role="menuitem">
              <MaterialIcon name="chevron_right" size={18} />
              <span>{category.name}</span>
            </button>
          ))}
          {!categories.length ? (
            <span className="search-form__category-empty">{categoriesLoading ? "Loading categories..." : categoriesError || "No categories found."}</span>
          ) : null}
        </div>
      ) : null}
      {suggestionsOpen && suggestions.length ? (
        <div className="search-suggestions" role="listbox">
          {suggestions.map((item) => (
            <button
              type="button"
              key={`${item.type}-${item.id}`}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => openSuggestion(item.title)}
              role="option"
            >
              <MaterialIcon name="search" size={18} />
              <span>{item.title}</span>
            </button>
          ))}
        </div>
      ) : null}
    </form>
  );
}
