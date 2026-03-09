from django.urls import path

from .views import ProductSearchAPIView

urlpatterns = [
    path('', ProductSearchAPIView.as_view(), name='product-search'),
]
