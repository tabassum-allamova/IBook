"""
Wave 1: User profile endpoint tests.

Endpoints:
  GET   /api/auth/profile/  — retrieve current user's profile
  PATCH /api/auth/profile/  — update allowed profile fields
"""

import pytest


@pytest.mark.django_db
def test_get_profile(auth_client, customer_user):
    """GET /api/auth/profile/ returns the authenticated user's profile fields."""
    client = auth_client(customer_user)
    response = client.get("/api/auth/profile/")
    assert response.status_code == 200
    assert response.data["email"] == "customer@test.com"
    assert response.data["role"] == "CUSTOMER"
    assert "phone_number" in response.data
    assert "avatar" in response.data


@pytest.mark.django_db
def test_update_profile(auth_client, customer_user):
    """PATCH /api/auth/profile/ updates allowed fields and returns 200."""
    client = auth_client(customer_user)
    payload = {"phone_number": "+9876543210"}
    response = client.patch("/api/auth/profile/", payload)
    assert response.status_code == 200
    assert response.data["phone_number"] == "+9876543210"


@pytest.mark.django_db
def test_cannot_change_role(auth_client, customer_user):
    """PATCH /api/auth/profile/ with a 'role' field is either ignored or returns 400."""
    client = auth_client(customer_user)
    payload = {"role": "BARBER"}
    response = client.patch("/api/auth/profile/", payload)
    # Either 400 (role field rejected) or 200 with role unchanged
    if response.status_code == 200:
        assert response.data["role"] == "CUSTOMER"
    else:
        assert response.status_code == 400
