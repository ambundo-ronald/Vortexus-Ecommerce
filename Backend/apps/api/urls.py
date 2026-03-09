from django.urls import include, path

from .views import CategoryListAPIView, ProductDetailAPIView, ProductListAPIView, QuoteRequestAPIView

urlpatterns = [
    path('catalog/categories/', CategoryListAPIView.as_view(), name='catalog-categories'),
    path('catalog/products/', ProductListAPIView.as_view(), name='catalog-products'),
    path('catalog/products/<int:product_id>/', ProductDetailAPIView.as_view(), name='catalog-product-detail'),
    path('quotes/', QuoteRequestAPIView.as_view(), name='quote-request'),
    path('search/', include('apps.search.urls')),
    path('search/image/', include('apps.image_search.urls')),
    path('recommendations/', include('apps.recommendations.urls')),
]
