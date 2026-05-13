import { useEffect } from "react";
import { useLocation } from "react-router-dom";

import { trackStorefrontEvent } from "../../utils/analytics";

export default function AnalyticsTracker() {
  const location = useLocation();

  useEffect(() => {
    if (location.pathname.startsWith("/admin") || location.pathname.startsWith("/supplier")) return;
    trackStorefrontEvent("page_view", {
      path: `${location.pathname}${location.search}`,
      title: document.title,
      referrer: document.referrer
    });
  }, [location.pathname, location.search]);

  return null;
}
