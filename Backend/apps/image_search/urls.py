from django.urls import path

from .views import ImageSearchAPIView

urlpatterns = [
    path('', ImageSearchAPIView.as_view(), name='image-search'),
]
