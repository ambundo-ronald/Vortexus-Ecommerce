import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { siteTranslationKeys } from "../../locales/siteTranslations.generated.js";

const translatedTextNodes = new WeakMap();
const translatedAttributes = new WeakMap();
const localizableAttributes = ["placeholder", "aria-label", "title"];

function normalize(value) {
  return value.replace(/\s+/g, " ").trim();
}

function translateTextNode(node, t) {
  if (node.parentElement?.closest("script, style, code, pre, [contenteditable='true']")) return;

  const original = translatedTextNodes.get(node) ?? node.nodeValue;
  const phrase = normalize(original || "");
  const key = siteTranslationKeys[phrase];
  if (!key) return;

  translatedTextNodes.set(node, original);
  const leadingSpace = original.match(/^\s*/)?.[0] || "";
  const trailingSpace = original.match(/\s*$/)?.[0] || "";
  const translated = `${leadingSpace}${t(key)}${trailingSpace}`;
  if (node.nodeValue !== translated) node.nodeValue = translated;
}

function translateElementAttributes(element, t) {
  const originals = translatedAttributes.get(element) || {};
  let changed = false;

  for (const attribute of localizableAttributes) {
    if (!element.hasAttribute(attribute)) continue;
    const original = originals[attribute] ?? element.getAttribute(attribute);
    const key = siteTranslationKeys[normalize(original || "")];
    if (!key) continue;

    originals[attribute] = original;
    const translated = t(key);
    if (element.getAttribute(attribute) !== translated) element.setAttribute(attribute, translated);
    changed = true;
  }

  if (changed) translatedAttributes.set(element, originals);
}

function translateTree(root, t) {
  if (root.nodeType === Node.TEXT_NODE) {
    translateTextNode(root, t);
    return;
  }
  if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) return;

  if (root.nodeType === Node.ELEMENT_NODE) translateElementAttributes(root, t);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    if (node.nodeType === Node.TEXT_NODE) translateTextNode(node, t);
    else translateElementAttributes(node, t);
    node = walker.nextNode();
  }
}

export default function SiteLocalizer() {
  const { t, i18n } = useTranslation();

  useEffect(() => {
    const root = document.getElementById("root");
    if (!root) return undefined;

    translateTree(root, t);
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "characterData") translateTextNode(mutation.target, t);
        if (mutation.type === "attributes") translateElementAttributes(mutation.target, t);
        mutation.addedNodes.forEach((node) => translateTree(node, t));
      }
    });
    observer.observe(root, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: localizableAttributes,
    });

    return () => observer.disconnect();
  }, [i18n.resolvedLanguage, t]);

  return null;
}
