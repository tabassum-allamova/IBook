"""
Wave 0 stubs: Role-based permission tests.

These tests verify that the custom DRF permission classes correctly block
users from accessing endpoints outside their role. Implementation in Plan 01-02.
"""

import pytest


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_customer_blocked_from_barber_endpoint(auth_client, customer_user):
    """A Customer hitting a barber-only endpoint receives 403 Forbidden."""
    client = auth_client(customer_user)
    response = client.get("/api/barbers/dashboard/")
    assert response.status_code == 403


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_barber_blocked_from_owner_endpoint(auth_client, barber_user):
    """A Barber hitting a shop-owner-only endpoint receives 403 Forbidden."""
    client = auth_client(barber_user)
    response = client.get("/api/shops/dashboard/")
    assert response.status_code == 403


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_unauthenticated_blocked(api_client):
    """An unauthenticated request to a protected endpoint returns 401 Unauthorized."""
    response = api_client.get("/api/auth/profile/")
    assert response.status_code == 401
