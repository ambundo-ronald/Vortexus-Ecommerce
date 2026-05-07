import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { catalogApi } from "../../api/catalog.api";
import MaterialIcon from "../ui/MaterialIcon.jsx";

const VISIBLE_CATEGORY_COUNT = 5;

export default function CategoryNav({ categories = [], activeCategory = "", variant = "desktop" }) {
  const [fallbackCategories, setFallbackCategories] = useState([]);
  const [fallbackError, setFallbackError] = useState("");
  const [searchParams] = useSearchParams();
  const currentParams = Object.fromEntries(searchParams.entries());
  const resolvedCategories = useMemo(
    () => (categories.length ? categories : fallbackCategories),
    [categories, fallbackCategories]
  );
  const visibleCategories = resolvedCategories.slice(0, VISIBLE_CATEGORY_COUNT);
  const hiddenCategories = resolvedCategories.slice(VISIBLE_CATEGORY_COUNT);

  useEffect(() => {
    if (categories.length) return undefined;
    let cancelled = false;
    async function loadFallbackCategories() {
      try {
        const payload = await catalogApi.categories();
        const nextCategories = Array.isArray(payload) ? payload : payload.results || [];
        if (!cancelled) setFallbackCategories(nextCategories);
      } catch (error) {
        if (!cancelled) setFallbackError(error.normalized?.message || error.message || "Categories unavailable");
      }
    }
    void loadFallbackCategories();
    return () => {
      cancelled = true;
    };
  }, [categories.length]);

  function categoryUrl(category) {
    const next = new URLSearchParams(currentParams);
    next.delete("page");

    if (category?.slug) {
      next.set("category", category.slug);
    } else {
      next.delete("category");
    }

    const query = next.toString();
    return `/catalog${query ? `?${query}` : ""}`;
  }

  if (variant === "mobile") {
    return (
      <nav className="category-sidebar" aria-label="Product categories">
        <Link className={!activeCategory ? "active" : ""} to={categoryUrl(null)}>
          All
        </Link>
        {resolvedCategories.map((category) => (
          <Link
            key={category.id}
            className={activeCategory === category.slug ? "active" : ""}
            to={categoryUrl(category)}
          >
            {category.name}
          </Link>
        ))}
        {!resolvedCategories.length ? (
          <span className="category-sidebar__empty">{fallbackError || "Loading categories..."}</span>
        ) : null}
      </nav>
    );
  }

  return (
    <nav className="category-strip" aria-label="Product categories">
      <Link className={!activeCategory ? "category-link active" : "category-link"} to={categoryUrl(null)}>
        All
      </Link>
      {visibleCategories.map((category) => (
        <Link
          key={category.id}
          className={activeCategory === category.slug ? "category-link active" : "category-link"}
          to={categoryUrl(category)}
        >
          {category.name}
        </Link>
      ))}
      {hiddenCategories.length ? (
        <details className="category-more">
          <summary>
            More
            <MaterialIcon name="keyboard_arrow_down" size={18} />
          </summary>
          <div className="category-more__menu">
            {hiddenCategories.map((category) => (
              <Link
                key={category.id}
                className={activeCategory === category.slug ? "active" : ""}
                to={categoryUrl(category)}
              >
                {category.name}
              </Link>
            ))}
          </div>
        </details>
      ) : null}
      <div className="category-sidebar-fallback">
        <Link className={!activeCategory ? "active" : ""} to={categoryUrl(null)}>
          All
        </Link>
        {resolvedCategories.map((category) => (
          <Link
            key={category.id}
            className={activeCategory === category.slug ? "active" : ""}
            to={categoryUrl(category)}
          >
            {category.name}
          </Link>
        ))}
      </div>
    </nav>
  );
}
