import { useEffect } from "react";

const DEFAULT_TITLE = "Reesolmart | Just in time, buying";
const DEFAULT_DESCRIPTION = "Shop pumps, water treatment systems, filters, tanks, spares, and industrial supplies from Reesolmart.";
const DEFAULT_IMAGE = "/Reesolmart logo.png";

export default function Seo({
  title = DEFAULT_TITLE,
  description = DEFAULT_DESCRIPTION,
  canonicalPath = "/",
  image = DEFAULT_IMAGE,
  type = "website",
  robots = "",
  jsonLd = []
}) {
  useEffect(() => {
    if (typeof document === "undefined") return undefined;

    const previousTitle = document.title;
    const canonicalUrl = absoluteUrl(canonicalPath);
    const imageUrl = absoluteUrl(image);
    const cleanTitle = title || DEFAULT_TITLE;
    const cleanDescription = description || DEFAULT_DESCRIPTION;
    const schemas = Array.isArray(jsonLd) ? jsonLd.filter(Boolean) : [jsonLd].filter(Boolean);

    document.title = cleanTitle;

    const nodes = [
      metaTag("description", cleanDescription),
      robots ? metaTag("robots", robots) : null,
      linkTag("canonical", canonicalUrl),
      propertyTag("og:title", cleanTitle),
      propertyTag("og:description", cleanDescription),
      propertyTag("og:type", type),
      propertyTag("og:url", canonicalUrl),
      propertyTag("og:image", imageUrl),
      metaTag("twitter:card", "summary_large_image"),
      metaTag("twitter:title", cleanTitle),
      metaTag("twitter:description", cleanDescription),
      metaTag("twitter:image", imageUrl),
      ...schemas.map(jsonLdTag)
    ].filter(Boolean);

    nodes.forEach((node) => {
      if (!node.parentNode) document.head.appendChild(node);
    });

    return () => {
      document.title = previousTitle || DEFAULT_TITLE;
      nodes.forEach(restoreNode);
    };
  }, [canonicalPath, description, image, jsonLd, robots, title, type]);

  return null;
}

export function absoluteUrl(path = "/") {
  const raw = String(path || "/");
  if (/^https?:\/\//i.test(raw)) return raw;

  const origin = import.meta.env.VITE_STOREFRONT_ORIGIN || (typeof window !== "undefined" ? window.location.origin : "");
  if (!origin) return raw;

  return new URL(raw.startsWith("/") ? raw : `/${raw}`, origin).toString();
}

function metaTag(name, content) {
  const node = document.head.querySelector(`meta[name="${cssEscape(name)}"]`) || document.createElement("meta");
  prepareManagedNode(node, 'content');
  node.setAttribute("name", name);
  node.setAttribute("content", String(content || ""));
  return node;
}

function propertyTag(property, content) {
  const node = document.head.querySelector(`meta[property="${cssEscape(property)}"]`) || document.createElement("meta");
  prepareManagedNode(node, 'content');
  node.setAttribute("property", property);
  node.setAttribute("content", String(content || ""));
  return node;
}

function linkTag(rel, href) {
  const node = document.head.querySelector(`link[rel="${cssEscape(rel)}"]`) || document.createElement("link");
  prepareManagedNode(node, 'href');
  node.setAttribute("rel", rel);
  node.setAttribute("href", href);
  return node;
}

function jsonLdTag(value) {
  const node = document.createElement("script");
  node.type = "application/ld+json";
  node.textContent = JSON.stringify(value);
  node.dataset.reesolmartSeo = "true";
  node.dataset.reesolmartSeoCreated = "true";
  return node;
}

function prepareManagedNode(node, trackedAttribute) {
  node.dataset.reesolmartSeo = "true";
  node.dataset.reesolmartSeoTrackedAttribute = trackedAttribute;
  if (!node.parentNode) {
    node.dataset.reesolmartSeoCreated = "true";
    return;
  }
  if (!node.dataset.reesolmartSeoPreviousValue) {
    node.dataset.reesolmartSeoPreviousValue = node.getAttribute(trackedAttribute) || "";
  }
}

function restoreNode(node) {
  if (node.dataset.reesolmartSeoCreated === "true") {
    node.remove();
    return;
  }
  const trackedAttribute = node.dataset.reesolmartSeoTrackedAttribute;
  if (trackedAttribute) {
    node.setAttribute(trackedAttribute, node.dataset.reesolmartSeoPreviousValue || "");
  }
  delete node.dataset.reesolmartSeo;
  delete node.dataset.reesolmartSeoTrackedAttribute;
  delete node.dataset.reesolmartSeoPreviousValue;
}

function cssEscape(value = "") {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") return CSS.escape(value);
  return String(value).replace(/"/g, '\\"');
}
