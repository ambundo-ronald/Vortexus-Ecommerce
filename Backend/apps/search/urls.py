from django.urls import path

from .views import ProductSearchAPIView, ProductSearchSuggestionAPIView

urlpatterns = [
    path('suggestions/', ProductSearchSuggestionAPIView.as_view(), name='product-search-suggestions'),
    path('', ProductSearchAPIView.as_view(), name='product-search'),
]
