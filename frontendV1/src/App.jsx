import AppRouter from "./router/index.jsx";
import AnalyticsTracker from "./components/analytics/AnalyticsTracker.jsx";
import ScrollToTop from "./components/layout/ScrollToTop.jsx";
import SiteLocalizer from "./components/localization/SiteLocalizer.jsx";

export default function App() {
  return (
    <>
      <ScrollToTop />
      <AnalyticsTracker />
      <AppRouter />
      <SiteLocalizer />
    </>
  );
}
