"""
Wave 1: Logout endpoint tests.

Endpoints:
  POST /api/auth/logout/ — blacklist refresh token and clear httpOnly cookie
"""

import pytest


@pytest.mark.django_db
def test_logout(auth_client, customer_user):
    """POST /api/auth/logout/ with a valid access token returns 200."""
    client = auth_client(customer_user)
    response = client.post("/api/auth/logout/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_clears_cookie(auth_client, customer_user):
    """POST /api/auth/logout/ response includes a Set-Cookie header that clears the refresh_token cookie."""
    client = auth_client(customer_user)
    response = client.post("/api/auth/logout/")
    assert response.status_code == 200
    # Cookie should be cleared (max-age=0 or expires in the past)
    assert "refresh_token" in response.cookies
    cookie = response.cookies["refresh_token"]
    assert cookie["max-age"] == 0 or cookie["expires"] != ""
