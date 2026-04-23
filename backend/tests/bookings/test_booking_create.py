"""
Integration tests for booking creation endpoint.

Wave 0 RED state: views and URLs do not exist yet.
These tests will fail with 404 until Plan 02 implements the views.
"""

import datetime

import pytest

from apps.bookings.models import Appointment, AppointmentService


BOOKINGS_URL = '/api/bookings/'


@pytest.mark.django_db
class TestCreateBooking:
    """Tests for POST /api/bookings/."""

    def _next_monday(self):
        today = datetime.date.today()
        return today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)

    def test_create_booking_success(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        response = client.post(
            BOOKINGS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': self._next_monday().isoformat(),
                'start_time': '09:00',
                'service_ids': [service_fixture.pk],
                'payment_method': 'AT_SHOP',
            },
            format='json',
        )
        assert response.status_code == 201
        assert response.data['status'] == 'CONFIRMED'
        assert response.data['barber'] == barber_with_schedule.pk
        assert Appointment.objects.count() == 1

    def test_create_booking_overlap_returns_409(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        monday = self._next_monday()
        payload = {
            'barber_id': barber_with_schedule.pk,
            'date': monday.isoformat(),
            'start_time': '09:00',
            'service_ids': [service_fixture.pk],
            'payment_method': 'AT_SHOP',
        }
        # First booking should succeed
        response1 = client.post(BOOKINGS_URL, payload, format='json')
        assert response1.status_code == 201

        # Overlapping booking should return 409
        response2 = client.post(BOOKINGS_URL, payload, format='json')
        assert response2.status_code == 409

    def test_create_booking_online_payment(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        """ONLINE bookings start PENDING; they only flip to PAID once Stripe
        confirms the charge (via webhook or the finalize endpoint). The
        earlier behavior of marking them PAID up-front let customers hold a
        slot without paying."""
        client = auth_client(customer_user)
        response = client.post(
            BOOKINGS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': self._next_monday().isoformat(),
                'start_time': '09:00',
                'service_ids': [service_fixture.pk],
                'payment_method': 'ONLINE',
            },
            format='json',
        )
        assert response.status_code == 201
        assert response.data['payment_status'] == 'PENDING'

    def test_create_booking_pay_at_shop(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        client = auth_client(customer_user)
        response = client.post(
            BOOKINGS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': self._next_monday().isoformat(),
                'start_time': '09:00',
                'service_ids': [service_fixture.pk],
                'payment_method': 'AT_SHOP',
            },
            format='json',
        )
        assert response.status_code == 201
        assert response.data['payment_status'] == 'PENDING'

    def test_create_booking_multi_service(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        """Two services -> total_price = sum, total_duration = sum, end_time correct."""
        from apps.services.models import Service

        service2 = Service.objects.create(
            barber=barber_with_schedule,
            name='Beard Trim',
            price=30000,
            duration_minutes=15,
        )
        client = auth_client(customer_user)
        response = client.post(
            BOOKINGS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': self._next_monday().isoformat(),
                'start_time': '09:00',
                'service_ids': [service_fixture.pk, service2.pk],
                'payment_method': 'AT_SHOP',
            },
            format='json',
        )
        assert response.status_code == 201
        assert response.data['total_price'] == 80000  # 50000 + 30000
        assert response.data['total_duration'] == 45  # 30 + 15
        assert response.data['end_time'] == '09:45'
        assert AppointmentService.objects.count() == 2

    def test_non_customer_cannot_book(
        self, auth_client, barber_user, barber_with_schedule, service_fixture,
    ):
        """Barber tries to book -> 403."""
        client = auth_client(barber_user)
        response = client.post(
            BOOKINGS_URL,
            {
                'barber_id': barber_with_schedule.pk,
                'date': self._next_monday().isoformat(),
                'start_time': '09:00',
                'service_ids': [service_fixture.pk],
                'payment_method': 'AT_SHOP',
            },
            format='json',
        )
        assert response.status_code == 403
