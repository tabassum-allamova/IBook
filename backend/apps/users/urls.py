"""
URL patterns for all IBook auth endpoints.

Mounted at /api/auth/ in config/urls.py.
"""

from django.urls import path

from apps.users.views import (
    CookieTokenRefreshView,
    CustomerRegisterView,
    LoginView,
    LogoutView,
    ProfessionalRegisterView,
    ProfileView,
    VerifyEmailView,
)

app_name = "users"

urlpatterns = [
    path("register/customer/", CustomerRegisterView.as_view(), name="register-customer"),
    path("register/professional/", ProfessionalRegisterView.as_view(), name="register-professional"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
