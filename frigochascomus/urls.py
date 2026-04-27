from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/',    include('orders.api_urls')),
    path('admin/',  include('orders.admin_urls')),
    path('',        include('orders.site_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
