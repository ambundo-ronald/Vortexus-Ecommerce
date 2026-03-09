from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.common.views import IndustrialHomeView

oscar_urlpatterns, _, _ = apps.get_app_config('oscar').urls

urlpatterns = [
    path('', IndustrialHomeView.as_view(), name='industrial-home'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
    # Oscar internally uses namespaces like 'catalogue', so include raw patterns.
    path('', include(oscar_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
