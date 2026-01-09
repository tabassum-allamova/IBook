"""
Wave 0 stubs: Registration endpoint tests.

These tests define the expected behaviour of the registration endpoints
that will be implemented in Plan 01-02. All are skipped until then.

Endpoints (expected):
  POST /api/auth/register/customer/   — register a new Customer
  POST /api/auth/register/professional/ — register a new Barber or Shop Owner
"""

import pytest


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_register_customer(api_client):
    """POST /api/auth/register/customer/ with valid data returns 201."""
    payload = {
        "email": "newcustomer@test.com",
        "username": "newcustomer",
        "password": "Test1234",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone_number": "+1234567890",
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 201
    assert response.data["email"] == payload["email"]
    assert response.data["role"] == "CUSTOMER"


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_register_barber(api_client):
    """POST /api/auth/register/professional/ with role=BARBER returns 201."""
    payload = {
        "email": "newbarber@test.com",
        "username": "newbarber",
        "password": "Test1234",
        "role": "BARBER",
        "first_name": "Bob",
        "last_name": "Cuts",
        "years_of_experience": 5,
    }
    response = api_client.post("/api/auth/register/professional/", payload)
    assert response.status_code == 201
    assert response.data["role"] == "BARBER"


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_duplicate_email(api_client, customer_user):
    """POST with an already-registered email returns 400."""
    payload = {
        "email": "customer@test.com",  # same as customer_user fixture
        "username": "anothercustomer",
        "password": "Test1234",
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 400


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_weak_password(api_client):
    """POST with a password that contains no number returns 400."""
    payload = {
        "email": "weakpass@test.com",
        "username": "weakpass",
        "password": "password",  # no number — violates password policy
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 400


@pytest.mark.skip(reason="Endpoint not yet implemented — Plan 02")
def test_email_verification_sent(api_client, mocker):
    """Successful registration triggers a SendGrid verification email."""
    mock_send = mocker.patch("django.core.mail.send_mail")
    payload = {
        "email": "verify@test.com",
        "username": "verifyuser",
        "password": "Test1234",
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 201
    mock_send.assert_called_once()
