import { Route, Routes } from "react-router-dom";

import PageWrapper from "../components/layout/PageWrapper.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import SupplierRoute from "./SupplierRoute.jsx";
import AccountDashboardPage from "../pages/account/AccountDashboardPage.jsx";
import AccountDeletePage from "../pages/account/AccountDeletePage.jsx";
import AddressesPage from "../pages/account/AddressesPage.jsx";
import MessageDetailPage from "../pages/account/MessageDetailPage.jsx";
import MessagesPage from "../pages/account/MessagesPage.jsx";
import NotificationDetailPage from "../pages/account/NotificationDetailPage.jsx";
import NotificationsPage from "../pages/account/NotificationsPage.jsx";
import OrderDetailPage from "../pages/account/OrderDetailPage.jsx";
import OrdersPage from "../pages/account/OrdersPage.jsx";
import PreferencesPage from "../pages/account/PreferencesPage.jsx";
import ProfilePage from "../pages/account/ProfilePage.jsx";
import ProductAlertsPage from "../pages/account/ProductAlertsPage.jsx";
import RecentlyViewedPage from "../pages/account/RecentlyViewedPage.jsx";
import ReviewsPage from "../pages/account/ReviewsPage.jsx";
import WishlistPage from "../pages/account/WishlistPage.jsx";
import CartPage from "../pages/checkout/CartPage.jsx";
import CheckoutReviewPage from "../pages/checkout/CheckoutReviewPage.jsx";
import OrderConfirmationPage from "../pages/checkout/OrderConfirmationPage.jsx";
import PaymentPage from "../pages/checkout/PaymentPage.jsx";
import ShippingPage from "../pages/checkout/ShippingPage.jsx";
import NotFoundPage from "../pages/errors/NotFoundPage.jsx";
import UnauthorizedPage from "../pages/errors/UnauthorizedPage.jsx";
import ForgotPasswordPage from "../pages/auth/ForgotPasswordPage.jsx";
import LoginPage from "../pages/auth/LoginPage.jsx";
import RegisterPage from "../pages/auth/RegisterPage.jsx";
import ResetPasswordPage from "../pages/auth/ResetPasswordPage.jsx";
import VerifyEmailPage from "../pages/auth/VerifyEmailPage.jsx";
import CategoryPage from "../pages/public/CategoryPage.jsx";
import BrandPage from "../pages/public/BrandPage.jsx";
import GuestOrderDetailPage from "../pages/public/GuestOrderDetailPage.jsx";
import GuestOrderLookupPage from "../pages/public/GuestOrderLookupPage.jsx";
import HomePage from "../pages/public/HomePage.jsx";
import OfferDetailPage from "../pages/public/OfferDetailPage.jsx";
import OffersPage from "../pages/public/OffersPage.jsx";
import ProductAlertActionPage from "../pages/public/ProductAlertActionPage.jsx";
import ProductDetailPage from "../pages/public/ProductDetailPage.jsx";
import ProductListPage from "../pages/public/ProductListPage.jsx";
import RangeDetailPage from "../pages/public/RangeDetailPage.jsx";
import QuoteRequestPage from "../pages/public/QuoteRequestPage.jsx";
import SearchPage from "../pages/public/SearchPage.jsx";
import SharedWishlistPage from "../pages/public/SharedWishlistPage.jsx";
import SupplierDashboardPage from "../pages/supplier/SupplierDashboardPage.jsx";
import SupplierApplyPage from "../pages/supplier/SupplierApplyPage.jsx";
import SupplierOrderDetailPage from "../pages/supplier/SupplierOrderDetailPage.jsx";
import SupplierOrdersPage from "../pages/supplier/SupplierOrdersPage.jsx";
import SupplierProductsPage from "../pages/supplier/SupplierProductsPage.jsx";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<PageWrapper><HomePage /></PageWrapper>} />
      <Route path="/catalog" element={<PageWrapper><ProductListPage /></PageWrapper>} />
      <Route path="/catalog/brand/:brandSlug" element={<PageWrapper><BrandPage /></PageWrapper>} />
      <Route path="/catalog/category/:categorySlug" element={<PageWrapper><CategoryPage /></PageWrapper>} />
      <Route path="/products/:productId" element={<PageWrapper><ProductDetailPage /></PageWrapper>} />
      <Route path="/quote" element={<PageWrapper><ProtectedRoute><QuoteRequestPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/offers" element={<PageWrapper><OffersPage /></PageWrapper>} />
      <Route path="/offers/:offerSlug" element={<PageWrapper><OfferDetailPage /></PageWrapper>} />
      <Route path="/catalog/ranges/:rangeSlug" element={<PageWrapper><RangeDetailPage /></PageWrapper>} />
      <Route path="/search" element={<PageWrapper><SearchPage /></PageWrapper>} />
      <Route path="/orders/track" element={<PageWrapper><GuestOrderLookupPage /></PageWrapper>} />
      <Route path="/orders/track/:orderNumber/:hash" element={<PageWrapper><GuestOrderDetailPage /></PageWrapper>} />
      <Route path="/product-alerts/confirm/:key" element={<PageWrapper><ProductAlertActionPage action="confirm" /></PageWrapper>} />
      <Route path="/product-alerts/cancel/:key" element={<PageWrapper><ProductAlertActionPage action="cancel" /></PageWrapper>} />
      <Route path="/wishlists/shared/:key" element={<PageWrapper><SharedWishlistPage /></PageWrapper>} />
      <Route path="/checkout/cart" element={<PageWrapper><CartPage /></PageWrapper>} />
      <Route path="/checkout/shipping" element={<PageWrapper><ProtectedRoute><ShippingPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/checkout/payment" element={<PageWrapper><ProtectedRoute><PaymentPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/checkout/review" element={<PageWrapper><ProtectedRoute><CheckoutReviewPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/checkout/confirmation" element={<PageWrapper><ProtectedRoute><OrderConfirmationPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/login" element={<PageWrapper><LoginPage /></PageWrapper>} />
      <Route path="/register" element={<PageWrapper><RegisterPage /></PageWrapper>} />
      <Route path="/forgot-password" element={<PageWrapper><ForgotPasswordPage /></PageWrapper>} />
      <Route path="/reset-password" element={<PageWrapper><ResetPasswordPage /></PageWrapper>} />
      <Route path="/account/verify-email" element={<PageWrapper><VerifyEmailPage /></PageWrapper>} />
      <Route path="/unauthorized" element={<PageWrapper><UnauthorizedPage /></PageWrapper>} />
      <Route path="/account" element={<PageWrapper><ProtectedRoute><AccountDashboardPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/delete" element={<PageWrapper><ProtectedRoute><AccountDeletePage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/addresses" element={<PageWrapper><ProtectedRoute><AddressesPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/profile" element={<PageWrapper><ProtectedRoute><ProfilePage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/messages" element={<PageWrapper><ProtectedRoute><MessagesPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/messages/:messageId" element={<PageWrapper><ProtectedRoute><MessageDetailPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/notifications" element={<PageWrapper><ProtectedRoute><NotificationsPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/notifications/:notificationId" element={<PageWrapper><ProtectedRoute><NotificationDetailPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/orders" element={<PageWrapper><ProtectedRoute><OrdersPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/orders/:orderNumber" element={<PageWrapper><ProtectedRoute><OrderDetailPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/preferences" element={<PageWrapper><ProtectedRoute><PreferencesPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/product-alerts" element={<PageWrapper><ProtectedRoute><ProductAlertsPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/recently-viewed" element={<PageWrapper><RecentlyViewedPage /></PageWrapper>} />
      <Route path="/account/wishlist" element={<PageWrapper><ProtectedRoute><WishlistPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/reviews" element={<PageWrapper><ProtectedRoute><ReviewsPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/supplier/apply" element={<PageWrapper><ProtectedRoute><SupplierApplyPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/supplier" element={<PageWrapper><SupplierRoute><SupplierDashboardPage /></SupplierRoute></PageWrapper>} />
      <Route path="/supplier/products" element={<PageWrapper><SupplierRoute requireApproved><SupplierProductsPage /></SupplierRoute></PageWrapper>} />
      <Route path="/supplier/orders" element={<PageWrapper><SupplierRoute requireApproved><SupplierOrdersPage /></SupplierRoute></PageWrapper>} />
      <Route path="/supplier/orders/:orderNumber" element={<PageWrapper><SupplierRoute requireApproved><SupplierOrderDetailPage /></SupplierRoute></PageWrapper>} />
      <Route path="*" element={<PageWrapper><NotFoundPage /></PageWrapper>} />
    </Routes>
  );
}
