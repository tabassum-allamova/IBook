"""
BARB-02/BARB-03: Barber availability schedule and block tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-04 implements the availability app.
"""

import pytest


@pytest.mark.django_db
def test_weekly_schedule_save(auth_client, barber_user):
    """Barber can PUT /api/availability/schedule/ with 7-day array → 200."""
    client = auth_client(barber_user)
    schedule = [
        {'weekday': i, 'start_time': '09:00', 'end_time': '18:00', 'is_working': True}
        for i in range(7)
    ]
    response = client.put('/api/availability/schedule/', schedule, format='json')
    assert response.status_code == 200


@pytest.mark.django_db
def test_weekly_schedule_all_days(auth_client, barber_user):
    """GET /api/availability/schedule/ → 200 with exactly 7 day rows."""
    client = auth_client(barber_user)
    response = client.get('/api/availability/schedule/')
    assert response.status_code == 200
    assert len(response.data) == 7


@pytest.mark.django_db
def test_block_full_date(auth_client, barber_user):
    """Barber can POST /api/availability/blocks/ with {date} only → 201 full-day block."""
    client = auth_client(barber_user)
    payload = {'date': '2026-06-01'}
    response = client.post('/api/availability/blocks/', payload, format='json')
    assert response.status_code == 201
    # Full-day block: block_start and block_end should be absent or null
    assert response.data.get('block_start') in (None, '')
    assert response.data.get('block_end') in (None, '')


@pytest.mark.django_db
def test_block_partial_time(auth_client, barber_user):
    """Barber can POST /api/availability/blocks/ with {date, block_start, block_end} → 201 partial block."""
    client = auth_client(barber_user)
    payload = {
        'date': '2026-06-02',
        'block_start': '12:00',
        'block_end': '14:00',
    }
    response = client.post('/api/availability/blocks/', payload, format='json')
    assert response.status_code == 201
    assert response.data['block_start'] == '12:00:00'
    assert response.data['block_end'] == '14:00:00'
