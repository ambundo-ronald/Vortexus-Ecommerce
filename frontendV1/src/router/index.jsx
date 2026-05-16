import { Route, Routes } from "react-router-dom";

import PageWrapper from "../components/layout/PageWrapper.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import AccountDashboardPage from "../pages/account/AccountDashboardPage.jsx";
import AddressesPage from "../pages/account/AddressesPage.jsx";
import OrderDetailPage from "../pages/account/OrderDetailPage.jsx";
import OrdersPage from "../pages/account/OrdersPage.jsx";
import ProfilePage from "../pages/account/ProfilePage.jsx";
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
import HomePage from "../pages/public/HomePage.jsx";
import ProductDetailPage from "../pages/public/ProductDetailPage.jsx";
import ProductListPage from "../pages/public/ProductListPage.jsx";
import QuoteRequestPage from "../pages/public/QuoteRequestPage.jsx";
import SearchPage from "../pages/public/SearchPage.jsx";
import SharedWishlistPage from "../pages/public/SharedWishlistPage.jsx";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<PageWrapper><HomePage /></PageWrapper>} />
      <Route path="/catalog" element={<PageWrapper><ProductListPage /></PageWrapper>} />
      <Route path="/catalog/category/:categorySlug" element={<PageWrapper><CategoryPage /></PageWrapper>} />
      <Route path="/products/:productId" element={<PageWrapper><ProductDetailPage /></PageWrapper>} />
      <Route path="/quote" element={<PageWrapper><QuoteRequestPage /></PageWrapper>} />
      <Route path="/search" element={<PageWrapper><SearchPage /></PageWrapper>} />
      <Route path="/wishlists/shared/:key" element={<PageWrapper><SharedWishlistPage /></PageWrapper>} />
      <Route path="/checkout/cart" element={<PageWrapper><CartPage /></PageWrapper>} />
      <Route path="/checkout/shipping" element={<PageWrapper><ShippingPage /></PageWrapper>} />
      <Route path="/checkout/payment" element={<PageWrapper><PaymentPage /></PageWrapper>} />
      <Route path="/checkout/review" element={<PageWrapper><CheckoutReviewPage /></PageWrapper>} />
      <Route path="/checkout/confirmation" element={<PageWrapper><OrderConfirmationPage /></PageWrapper>} />
      <Route path="/login" element={<PageWrapper><LoginPage /></PageWrapper>} />
      <Route path="/register" element={<PageWrapper><RegisterPage /></PageWrapper>} />
      <Route path="/forgot-password" element={<PageWrapper><ForgotPasswordPage /></PageWrapper>} />
      <Route path="/reset-password" element={<PageWrapper><ResetPasswordPage /></PageWrapper>} />
      <Route path="/account/verify-email" element={<PageWrapper><VerifyEmailPage /></PageWrapper>} />
      <Route path="/unauthorized" element={<PageWrapper><UnauthorizedPage /></PageWrapper>} />
      <Route path="/account" element={<PageWrapper><ProtectedRoute><AccountDashboardPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/addresses" element={<PageWrapper><ProtectedRoute><AddressesPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/profile" element={<PageWrapper><ProtectedRoute><ProfilePage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/orders" element={<PageWrapper><ProtectedRoute><OrdersPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/orders/:orderNumber" element={<PageWrapper><ProtectedRoute><OrderDetailPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/wishlist" element={<PageWrapper><ProtectedRoute><WishlistPage /></ProtectedRoute></PageWrapper>} />
      <Route path="/account/reviews" element={<PageWrapper><ProtectedRoute><ReviewsPage /></ProtectedRoute></PageWrapper>} />
      <Route path="*" element={<PageWrapper><NotFoundPage /></PageWrapper>} />
    </Routes>
  );
}
