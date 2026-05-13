import AppRouter from "./router/index.jsx";
import AnalyticsTracker from "./components/analytics/AnalyticsTracker.jsx";

export default function App() {
  return (
    <>
      <AnalyticsTracker />
      <AppRouter />
    </>
  );
}
