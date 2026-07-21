import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import PageWrapper from "../components/layout/PageWrapper.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import SupplierRoute from "./SupplierRoute.jsx";

const AccountDashboardPage = lazy(() => import("../pages/account/AccountDashboardPage.jsx"));
const AccountDeletePage = lazy(() => import("../pages/account/AccountDeletePage.jsx"));
const AddressesPage = lazy(() => import("../pages/account/AddressesPage.jsx"));
const MessageDetailPage = lazy(() => import("../pages/account/MessageDetailPage.jsx"));
const MessagesPage = lazy(() => import("../pages/account/MessagesPage.jsx"));
const NotificationDetailPage = lazy(() => import("../pages/account/NotificationDetailPage.jsx"));
const NotificationsPage = lazy(() => import("../pages/account/NotificationsPage.jsx"));
const OrderDetailPage = lazy(() => import("../pages/account/OrderDetailPage.jsx"));
const OrdersPage = lazy(() => import("../pages/account/OrdersPage.jsx"));
const PreferencesPage = lazy(() => import("../pages/account/PreferencesPage.jsx"));
const ProfilePage = lazy(() => import("../pages/account/ProfilePage.jsx"));
const ProductAlertsPage = lazy(() => import("../pages/account/ProductAlertsPage.jsx"));
const RecentlyViewedPage = lazy(() => import("../pages/account/RecentlyViewedPage.jsx"));
const ReviewsPage = lazy(() => import("../pages/account/ReviewsPage.jsx"));
const WishlistPage = lazy(() => import("../pages/account/WishlistPage.jsx"));
const CartPage = lazy(() => import("../pages/checkout/CartPage.jsx"));
const CheckoutReviewPage = lazy(() => import("../pages/checkout/CheckoutReviewPage.jsx"));
const OrderConfirmationPage = lazy(() => import("../pages/checkout/OrderConfirmationPage.jsx"));
const PaymentPage = lazy(() => import("../pages/checkout/PaymentPage.jsx"));
const ShippingPage = lazy(() => import("../pages/checkout/ShippingPage.jsx"));
const NotFoundPage = lazy(() => import("../pages/errors/NotFoundPage.jsx"));
const UnauthorizedPage = lazy(() => import("../pages/errors/UnauthorizedPage.jsx"));
const ForgotPasswordPage = lazy(() => import("../pages/auth/ForgotPasswordPage.jsx"));
const LoginPage = lazy(() => import("../pages/auth/LoginPage.jsx"));
const RegisterPage = lazy(() => import("../pages/auth/RegisterPage.jsx"));
const ResetPasswordPage = lazy(() => import("../pages/auth/ResetPasswordPage.jsx"));
const VerifyEmailPage = lazy(() => import("../pages/auth/VerifyEmailPage.jsx"));
const CategoryPage = lazy(() => import("../pages/public/CategoryPage.jsx"));
const BrandPage = lazy(() => import("../pages/public/BrandPage.jsx"));
const GuestOrderDetailPage = lazy(() => import("../pages/public/GuestOrderDetailPage.jsx"));
const GuestOrderLookupPage = lazy(() => import("../pages/public/GuestOrderLookupPage.jsx"));
const HomePage = lazy(() => import("../pages/public/HomePage.jsx"));
const OfferDetailPage = lazy(() => import("../pages/public/OfferDetailPage.jsx"));
const OffersPage = lazy(() => import("../pages/public/OffersPage.jsx"));
const ProductAlertActionPage = lazy(() => import("../pages/public/ProductAlertActionPage.jsx"));
const ProductDetailPage = lazy(() => import("../pages/public/ProductDetailPage.jsx"));
const ProductListPage = lazy(() => import("../pages/public/ProductListPage.jsx"));
const RangeDetailPage = lazy(() => import("../pages/public/RangeDetailPage.jsx"));
const QuoteRequestPage = lazy(() => import("../pages/public/QuoteRequestPage.jsx"));
const SearchPage = lazy(() => import("../pages/public/SearchPage.jsx"));
const SharedWishlistPage = lazy(() => import("../pages/public/SharedWishlistPage.jsx"));
const SupplierDashboardPage = lazy(() => import("../pages/supplier/SupplierDashboardPage.jsx"));
const SupplierApplyPage = lazy(() => import("../pages/supplier/SupplierApplyPage.jsx"));
const SupplierOrderDetailPage = lazy(() => import("../pages/supplier/SupplierOrderDetailPage.jsx"));
const SupplierOrdersPage = lazy(() => import("../pages/supplier/SupplierOrdersPage.jsx"));
const SupplierProductsPage = lazy(() => import("../pages/supplier/SupplierProductsPage.jsx"));

export default function AppRouter() {
  return (
    <Suspense fallback={<RouteLoader />}>
      <Routes>
        <Route path="/" element={withShell(<HomePage />)} />
        <Route path="/catalog" element={withShell(<ProductListPage />)} />
        <Route path="/catalog/brand/:brandSlug" element={withShell(<BrandPage />)} />
        <Route path="/catalog/category/:categorySlug" element={withShell(<CategoryPage />)} />
        <Route path="/products/*" element={withShell(<ProductDetailPage />)} />
        <Route path="/quote" element={withShell(<ProtectedRoute><QuoteRequestPage /></ProtectedRoute>)} />
        <Route path="/offers" element={withShell(<OffersPage />)} />
        <Route path="/offers/:offerSlug" element={withShell(<OfferDetailPage />)} />
        <Route path="/catalog/ranges/:rangeSlug" element={withShell(<RangeDetailPage />)} />
        <Route path="/search" element={withShell(<SearchPage />)} />
        <Route path="/orders/track" element={withShell(<GuestOrderLookupPage />)} />
        <Route path="/orders/track/:orderNumber/:hash" element={withShell(<GuestOrderDetailPage />)} />
        <Route path="/product-alerts/confirm/:key" element={withShell(<ProductAlertActionPage action="confirm" />)} />
        <Route path="/product-alerts/cancel/:key" element={withShell(<ProductAlertActionPage action="cancel" />)} />
        <Route path="/wishlists/shared/:key" element={withShell(<SharedWishlistPage />)} />
        <Route path="/checkout/cart" element={withShell(<CartPage />)} />
        <Route path="/checkout/shipping" element={withShell(<ProtectedRoute><ShippingPage /></ProtectedRoute>)} />
        <Route path="/checkout/payment" element={withShell(<ProtectedRoute><PaymentPage /></ProtectedRoute>)} />
        <Route path="/checkout/review" element={withShell(<ProtectedRoute><CheckoutReviewPage /></ProtectedRoute>)} />
        <Route path="/checkout/confirmation" element={withShell(<ProtectedRoute><OrderConfirmationPage /></ProtectedRoute>)} />
        <Route path="/login" element={withShell(<LoginPage />)} />
        <Route path="/register" element={withShell(<RegisterPage />)} />
        <Route path="/forgot-password" element={withShell(<ForgotPasswordPage />)} />
        <Route path="/reset-password" element={withShell(<ResetPasswordPage />)} />
        <Route path="/account/verify-email" element={withShell(<VerifyEmailPage />)} />
        <Route path="/unauthorized" element={withShell(<UnauthorizedPage />)} />
        <Route path="/account" element={withShell(<ProtectedRoute><AccountDashboardPage /></ProtectedRoute>)} />
        <Route path="/account/delete" element={withShell(<ProtectedRoute><AccountDeletePage /></ProtectedRoute>)} />
        <Route path="/account/addresses" element={withShell(<ProtectedRoute><AddressesPage /></ProtectedRoute>)} />
        <Route path="/account/profile" element={withShell(<ProtectedRoute><ProfilePage /></ProtectedRoute>)} />
        <Route path="/account/messages" element={withShell(<ProtectedRoute><MessagesPage /></ProtectedRoute>)} />
        <Route path="/account/messages/:messageId" element={withShell(<ProtectedRoute><MessageDetailPage /></ProtectedRoute>)} />
        <Route path="/account/notifications" element={withShell(<ProtectedRoute><NotificationsPage /></ProtectedRoute>)} />
        <Route path="/account/notifications/:notificationId" element={withShell(<ProtectedRoute><NotificationDetailPage /></ProtectedRoute>)} />
        <Route path="/account/orders" element={withShell(<ProtectedRoute><OrdersPage /></ProtectedRoute>)} />
        <Route path="/account/orders/:orderNumber" element={withShell(<ProtectedRoute><OrderDetailPage /></ProtectedRoute>)} />
        <Route path="/account/preferences" element={withShell(<ProtectedRoute><PreferencesPage /></ProtectedRoute>)} />
        <Route path="/account/product-alerts" element={withShell(<ProtectedRoute><ProductAlertsPage /></ProtectedRoute>)} />
        <Route path="/account/recently-viewed" element={withShell(<RecentlyViewedPage />)} />
        <Route path="/account/wishlist" element={withShell(<ProtectedRoute><WishlistPage /></ProtectedRoute>)} />
        <Route path="/account/reviews" element={withShell(<ProtectedRoute><ReviewsPage /></ProtectedRoute>)} />
        <Route path="/supplier/apply" element={withShell(<ProtectedRoute><SupplierApplyPage /></ProtectedRoute>)} />
        <Route path="/supplier" element={withShell(<SupplierRoute><SupplierDashboardPage /></SupplierRoute>)} />
        <Route path="/supplier/products" element={withShell(<SupplierRoute requireApproved><SupplierProductsPage /></SupplierRoute>)} />
        <Route path="/supplier/orders" element={withShell(<SupplierRoute requireApproved><SupplierOrdersPage /></SupplierRoute>)} />
        <Route path="/supplier/orders/:orderNumber" element={withShell(<SupplierRoute requireApproved><SupplierOrderDetailPage /></SupplierRoute>)} />
        <Route path="*" element={withShell(<NotFoundPage />)} />
      </Routes>
    </Suspense>
  );
}

function withShell(children) {
  return <PageWrapper>{children}</PageWrapper>;
}

function RouteLoader() {
  return <Spinner label="Loading page" />;
}
