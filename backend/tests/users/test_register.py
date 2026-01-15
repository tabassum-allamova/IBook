"""
Wave 1: Registration endpoint tests.

Endpoints:
  POST /api/auth/register/customer/   — register a new Customer
  POST /api/auth/register/professional/ — register a new Barber or Shop Owner
"""

import pytest
from unittest import mock


@pytest.mark.django_db
def test_register_customer(api_client):
    """POST /api/auth/register/customer/ with valid data returns 201."""
    payload = {
        "email": "newcustomer@test.com",
        "password": "Test1234",
        "full_name": "Jane Doe",
        "phone_number": "+1234567890",
    }
    with mock.patch("apps.users.views.send_mail"):
        response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 201
    assert response.data["email"] == payload["email"]
    assert response.data["role"] == "CUSTOMER"


@pytest.mark.django_db
def test_register_barber(api_client):
    """POST /api/auth/register/professional/ with role=BARBER returns 201."""
    payload = {
        "email": "newbarber@test.com",
        "password": "Test1234",
        "full_name": "Bob Cuts",
        "role": "BARBER",
    }
    with mock.patch("apps.users.views.send_mail"):
        response = api_client.post("/api/auth/register/professional/", payload)
    assert response.status_code == 201
    assert response.data["role"] == "BARBER"


@pytest.mark.django_db
def test_duplicate_email(api_client, customer_user):
    """POST with an already-registered email returns 400."""
    payload = {
        "email": "customer@test.com",  # same as customer_user fixture
        "password": "Test1234",
        "full_name": "Another Customer",
    }
    with mock.patch("apps.users.views.send_mail"):
        response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_weak_password(api_client):
    """POST with a password that contains no number returns 400."""
    payload = {
        "email": "weakpass@test.com",
        "password": "password",  # no number — violates password policy
        "full_name": "Weak Pass",
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_email_verification_sent(api_client, mocker):
    """Successful registration triggers a verification email."""
    mock_send = mocker.patch("apps.users.views.send_mail")
    payload = {
        "email": "verify@test.com",
        "password": "Test1234",
        "full_name": "Verify User",
    }
    response = api_client.post("/api/auth/register/customer/", payload)
    assert response.status_code == 201
    mock_send.assert_called_once()
