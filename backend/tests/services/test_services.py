"""
BARB-01: Barber service CRUD tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-03 implements the services app.
"""

import pytest


@pytest.mark.django_db
def test_barber_creates_service(auth_client, barber_user):
    """Barber can POST /api/services/ → 201 with {name, price, duration_minutes}."""
    client = auth_client(barber_user)
    payload = {
        'name': 'Haircut',
        'price': '15.00',
        'duration_minutes': 30,
    }
    response = client.post('/api/services/', payload, format='json')
    assert response.status_code == 201
    assert response.data['name'] == 'Haircut'
    assert response.data['duration_minutes'] == 30


@pytest.mark.django_db
def test_service_reorder(auth_client, barber_user):
    """Barber can PATCH /api/services/reorder/ with [{id, sort_order}] → 200."""
    client = auth_client(barber_user)
    # Empty reorder is still a valid operation
    response = client.patch(
        '/api/services/reorder/',
        [],
        format='json',
    )
    assert response.status_code == 200
