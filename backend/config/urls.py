"""
IBook URL configuration.

/api/auth/       — authentication endpoints (apps.users.urls)
/api/barbers/    — barber endpoints (stub in Phase 1; full in Phase 3)
/api/shops/      — shop owner endpoints (stub in Phase 1; full in Phase 3)
/admin/          — Django admin
/media/          — uploaded media files (debug only)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.users.views import BarberDashboardStubView, ShopOwnerDashboardStubView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls", namespace="users")),
    # Phase 1 stubs — will be replaced by full app url configs in Phase 3
    path("api/barbers/dashboard/", BarberDashboardStubView.as_view(), name="barbers-dashboard"),
    path("api/shops/dashboard/", ShopOwnerDashboardStubView.as_view(), name="shops-dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
