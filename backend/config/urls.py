from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.users.views import (
    BarberDashboardStubView,
    BarberListView,
    BarberProfileView,
    ShopOwnerDashboardStubView,
)
from apps.services.urls import services_urlpatterns, availability_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls", namespace="users")),
    path("api/shops/", include("apps.shops.urls")),
    path("api/services/", include((services_urlpatterns, "services"))),
    path("api/availability/", include((availability_urlpatterns, "availability"))),
    path("api/bookings/", include("apps.bookings.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/barbers/", BarberListView.as_view(), name="barber-list"),
    path("api/barbers/<int:pk>/", BarberProfileView.as_view(), name="barber-profile"),
    path("api/barbers/dashboard/", BarberDashboardStubView.as_view(), name="barbers-dashboard"),
    path("api/shops/dashboard/", ShopOwnerDashboardStubView.as_view(), name="shops-dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
