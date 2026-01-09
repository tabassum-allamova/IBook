"""
Wave 0 stubs: Login and token-refresh endpoint tests.

Endpoints (expected):
  POST /api/auth/login/          — obtain JWT token pair
  POST /api/auth/token/refresh/  — refresh access token using httpOnly cookie
"""

import pytest


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_login_success(api_client, customer_user):
    """POST /api/auth/login/ with valid credentials returns 200, access token, and refresh cookie."""
    payload = {"email": "customer@test.com", "password": "Test1234"}
    response = api_client.post("/api/auth/login/", payload)
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh_token" in response.cookies


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_login_invalid_credentials(api_client):
    """POST /api/auth/login/ with wrong password returns 401."""
    payload = {"email": "nobody@test.com", "password": "WrongPass1"}
    response = api_client.post("/api/auth/login/", payload)
    assert response.status_code == 401


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_token_refresh(api_client, customer_user):
    """POST /api/auth/token/refresh/ with a valid refresh cookie returns a new access token."""
    # First, log in to get a refresh cookie
    login_response = api_client.post(
        "/api/auth/login/", {"email": "customer@test.com", "password": "Test1234"}
    )
    assert login_response.status_code == 200

    # Use the refresh cookie to get a new access token
    response = api_client.post("/api/auth/token/refresh/")
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_unverified_user_blocked(api_client, db):
    """A user with is_email_verified=False cannot log in — returns 403."""
    from apps.users.models import CustomUser

    unverified = CustomUser.objects.create_user(
        username="unverified",
        email="unverified@test.com",
        password="Test1234",
        is_email_verified=False,
        is_active=True,
    )
    response = api_client.post(
        "/api/auth/login/", {"email": "unverified@test.com", "password": "Test1234"}
    )
    assert response.status_code == 403
