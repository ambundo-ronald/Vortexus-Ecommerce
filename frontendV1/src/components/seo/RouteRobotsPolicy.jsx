import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const NOINDEX_PREFIXES = [
  "/account",
  "/checkout",
  "/forgot-password",
  "/login",
  "/orders/track",
  "/product-alerts",
  "/quote",
  "/register",
  "/reset-password",
  "/search",
  "/supplier",
  "/unauthorized",
  "/wishlists/shared"
];

export default function RouteRobotsPolicy() {
  const { pathname } = useLocation();
  const shouldNoindex = NOINDEX_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));

  useEffect(() => {
    if (typeof document === "undefined" || !shouldNoindex) return undefined;

    const node = document.head.querySelector('meta[name="robots"]') || document.createElement("meta");
    const created = !node.parentNode;
    const previous = node.getAttribute("content") || "";

    node.setAttribute("name", "robots");
    node.setAttribute("content", "noindex, nofollow");
    if (created) document.head.appendChild(node);

    return () => {
      if (created) node.remove();
      else node.setAttribute("content", previous);
    };
  }, [shouldNoindex]);

  return null;
}
