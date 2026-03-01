"""
IBook URL configuration.

/api/auth/           — authentication endpoints (apps.users.urls)
/api/services/       — service catalog endpoints (apps.services)
/api/availability/   — weekly schedule and date block endpoints (apps.services)
/api/barbers/        — barber endpoints (stub in Phase 1; full in Phase 3)
/api/shops/          — shop owner endpoints (stub in Phase 1; full in Phase 3)
/admin/              — Django admin
/media/              — uploaded media files (debug only)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.users.views import BarberDashboardStubView, ShopOwnerDashboardStubView
from apps.services.urls import services_urlpatterns, availability_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls", namespace="users")),
    # Phase 2 shops app — full CRUD, photos, memberships
    path("api/shops/", include("apps.shops.urls")),
    # Services and availability (Phase 2)
    path("api/services/", include((services_urlpatterns, "services"))),
    path("api/availability/", include((availability_urlpatterns, "availability"))),
    # Bookings (Phase 3)
    path("api/bookings/", include("apps.bookings.urls")),
    # Phase 1 stubs — will be replaced by full app url configs in Phase 3
    path("api/barbers/dashboard/", BarberDashboardStubView.as_view(), name="barbers-dashboard"),
    path("api/shops/dashboard/", ShopOwnerDashboardStubView.as_view(), name="shops-dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
