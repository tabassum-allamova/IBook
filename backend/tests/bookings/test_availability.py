"""
Integration tests for slot availability endpoint.

Wave 0 RED state: views and URLs do not exist yet.
These tests will fail with 404 until Plan 02 implements the views.
"""

import datetime

import pytest

from apps.bookings.models import Appointment
from apps.services.models import DateBlock


SLOTS_URL = '/api/bookings/slots/'


@pytest.mark.django_db
class TestSlotsEndpoint:
    """Tests for GET /api/bookings/slots/."""

    def test_slots_endpoint_returns_slots(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        # Next Monday
        today = datetime.date.today()
        next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)

        response = client.get(
            SLOTS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': next_monday.isoformat(),
                'service_ids': str(service_fixture.pk),
            },
        )
        assert response.status_code == 200
        assert 'slots' in response.data
        assert isinstance(response.data['slots'], list)
        assert len(response.data['slots']) > 0

    def test_slots_endpoint_past_date_returns_empty(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        past_date = datetime.date(2020, 1, 6)  # A Monday

        response = client.get(
            SLOTS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': past_date.isoformat(),
                'service_ids': str(service_fixture.pk),
            },
        )
        assert response.status_code == 200
        assert response.data['slots'] == []

    def test_slots_endpoint_missing_params(self, auth_client, customer_user):
        client = auth_client(customer_user)
        response = client.get(SLOTS_URL)
        assert response.status_code == 400

    def test_slots_blocked_day_returns_empty(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        today = datetime.date.today()
        next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)

        # Full-day block (no specific times = whole day)
        DateBlock.objects.create(
            barber=barber_with_schedule,
            date=next_monday,
        )

        response = client.get(
            SLOTS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': next_monday.isoformat(),
                'service_ids': str(service_fixture.pk),
            },
        )
        assert response.status_code == 200
        assert response.data['slots'] == []
