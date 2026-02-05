"""
SHOP-01: Shop CRUD tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-02 implements the shops app.
"""

import pytest


@pytest.mark.django_db
def test_owner_creates_shop(auth_client, shop_owner_user):
    """Shop owner can POST /api/shops/ and get 201 with shop data."""
    client = auth_client(shop_owner_user)
    payload = {
        'name': 'Test Barbershop',
        'address': '1 Main St',
        'lat': '41.299496',
        'lng': '69.240073',
        'description': 'A test shop',
    }
    response = client.post('/api/shops/', payload, format='json')
    assert response.status_code == 201
    assert response.data['name'] == 'Test Barbershop'


@pytest.mark.django_db
def test_customer_cannot_create_shop(auth_client, customer_user):
    """Customer role cannot create shops — expects 403 Forbidden."""
    client = auth_client(customer_user)
    payload = {
        'name': 'Unauthorised Shop',
        'address': '2 Side St',
        'lat': '41.299496',
        'lng': '69.240073',
    }
    response = client.post('/api/shops/', payload, format='json')
    assert response.status_code == 403
