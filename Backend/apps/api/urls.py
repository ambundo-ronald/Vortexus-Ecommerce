from django.urls import include, path

from .account_views import (
    AccountLoginAPIView,
    AccountLogoutAPIView,
    AccountPasswordAPIView,
    AccountProfileAPIView,
    AccountRegisterAPIView,
    CsrfTokenAPIView,
)
from .checkout_views import (
    BasketAPIView,
    BasketItemCollectionAPIView,
    BasketLineDetailAPIView,
    ShippingAddressAPIView,
    ShippingMethodSelectionAPIView,
    ShippingStateAPIView,
)
from .review_views import AccountReviewCollectionAPIView, AccountReviewDetailAPIView, ProductReviewCollectionAPIView
from .supplier_views import (
    SupplierAdminCollectionAPIView,
    SupplierAdminDetailAPIView,
    SupplierDashboardAPIView,
    SupplierProductCollectionAPIView,
    SupplierProductDetailAPIView,
    SupplierProfileAPIView,
)
from .wishlist_views import (
    DefaultWishListAPIView,
    DefaultWishListItemCollectionAPIView,
    DefaultWishListItemDetailAPIView,
    WishListCollectionAPIView,
    WishListDetailAPIView,
    WishListItemCollectionAPIView,
    WishListItemDetailAPIView,
    WishListItemStatusAPIView,
)
from .views import CategoryListAPIView, ProductDetailAPIView, ProductListAPIView, QuoteRequestAPIView

urlpatterns = [
    path('account/csrf/', CsrfTokenAPIView.as_view(), name='account-csrf'),
    path('account/register/', AccountRegisterAPIView.as_view(), name='account-register'),
    path('account/login/', AccountLoginAPIView.as_view(), name='account-login'),
    path('account/logout/', AccountLogoutAPIView.as_view(), name='account-logout'),
    path('account/me/', AccountProfileAPIView.as_view(), name='account-profile'),
    path('account/password/', AccountPasswordAPIView.as_view(), name='account-password'),
    path('supplier/profile/', SupplierProfileAPIView.as_view(), name='supplier-profile'),
    path('supplier/dashboard/', SupplierDashboardAPIView.as_view(), name='supplier-dashboard'),
    path('supplier/products/', SupplierProductCollectionAPIView.as_view(), name='supplier-products'),
    path('supplier/products/<int:product_id>/', SupplierProductDetailAPIView.as_view(), name='supplier-product-detail'),
    path('admin/suppliers/', SupplierAdminCollectionAPIView.as_view(), name='admin-suppliers'),
    path('admin/suppliers/<int:supplier_id>/', SupplierAdminDetailAPIView.as_view(), name='admin-supplier-detail'),
    path('checkout/basket/', BasketAPIView.as_view(), name='checkout-basket'),
    path('checkout/basket/items/', BasketItemCollectionAPIView.as_view(), name='checkout-basket-items'),
    path('checkout/basket/items/<int:line_id>/', BasketLineDetailAPIView.as_view(), name='checkout-basket-line'),
    path('checkout/shipping/', ShippingStateAPIView.as_view(), name='checkout-shipping-state'),
    path('checkout/shipping/address/', ShippingAddressAPIView.as_view(), name='checkout-shipping-address'),
    path('checkout/shipping/select/', ShippingMethodSelectionAPIView.as_view(), name='checkout-shipping-select'),
    path('account/wishlist/', DefaultWishListAPIView.as_view(), name='account-wishlist-default'),
    path('account/wishlist/items/', DefaultWishListItemCollectionAPIView.as_view(), name='account-wishlist-items-default'),
    path(
        'account/wishlist/items/<int:product_id>/',
        DefaultWishListItemDetailAPIView.as_view(),
        name='account-wishlist-item-default',
    ),
    path('account/wishlist/status/', WishListItemStatusAPIView.as_view(), name='account-wishlist-status'),
    path('account/wishlists/', WishListCollectionAPIView.as_view(), name='account-wishlists'),
    path('account/wishlists/<int:wishlist_id>/', WishListDetailAPIView.as_view(), name='account-wishlist-detail'),
    path(
        'account/wishlists/<int:wishlist_id>/items/',
        WishListItemCollectionAPIView.as_view(),
        name='account-wishlist-items',
    ),
    path(
        'account/wishlists/<int:wishlist_id>/items/<int:product_id>/',
        WishListItemDetailAPIView.as_view(),
        name='account-wishlist-item',
    ),
    path('account/reviews/', AccountReviewCollectionAPIView.as_view(), name='account-reviews'),
    path('account/reviews/<int:review_id>/', AccountReviewDetailAPIView.as_view(), name='account-review-detail'),
    path('catalog/categories/', CategoryListAPIView.as_view(), name='catalog-categories'),
    path('catalog/products/', ProductListAPIView.as_view(), name='catalog-products'),
    path('catalog/products/<int:product_id>/', ProductDetailAPIView.as_view(), name='catalog-product-detail'),
    path('catalog/products/<int:product_id>/reviews/', ProductReviewCollectionAPIView.as_view(), name='catalog-product-reviews'),
    path('quotes/', QuoteRequestAPIView.as_view(), name='quote-request'),
    path('search/', include('apps.search.urls')),
    path('search/image/', include('apps.image_search.urls')),
    path('recommendations/', include('apps.recommendations.urls')),
]
