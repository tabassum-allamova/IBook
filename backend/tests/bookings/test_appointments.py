"""
Integration tests for appointment management endpoints.

Wave 0 RED state: views and URLs do not exist yet.
These tests will fail with 404 until Plan 02 implements the views.
"""

import datetime

import pytest

from apps.bookings.models import Appointment, AppointmentService


@pytest.mark.django_db
class TestCustomerAppointments:
    """Tests for customer appointment listing and cancellation."""

    def _create_appointment(self, customer, barber, service, date, start_time, status='CONFIRMED'):
        appt = Appointment.objects.create(
            customer=customer,
            barber=barber,
            date=date,
            start_time=start_time,
            end_time=(
                datetime.datetime.combine(date, start_time)
                + datetime.timedelta(minutes=service.duration_minutes)
            ).time(),
            status=status,
            payment_method='AT_SHOP',
            payment_status='PENDING',
            total_price=service.price,
            total_duration=service.duration_minutes,
        )
        AppointmentService.objects.create(
            appointment=appt,
            service=service,
            service_name=service.name,
            service_price=service.price,
            service_duration=service.duration_minutes,
        )
        return appt

    def _next_monday(self):
        today = datetime.date.today()
        return today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)

    def test_customer_upcoming_list(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(customer_user)
        response = client.get('/api/bookings/my/upcoming/')
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_customer_past_list(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        past_date = datetime.date(2025, 1, 6)  # A past Monday
        self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            past_date, datetime.time(10, 0), status='COMPLETED',
        )
        client = auth_client(customer_user)
        response = client.get('/api/bookings/my/past/')
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_customer_cancel(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        appt = self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(customer_user)
        response = client.post(f'/api/bookings/{appt.pk}/cancel/')
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == 'CANCELLED'

    def test_customer_cannot_cancel_others_appointment(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        """Customer A cannot cancel Customer B's appointment."""
        from apps.users.models import CustomUser

        customer_b = CustomUser.objects.create_user(
            username='customer_b',
            email='customer_b@test.com',
            password='Test1234',
            role=CustomUser.Role.CUSTOMER,
            is_email_verified=True,
            is_active=True,
        )
        monday = self._next_monday()
        appt = self._create_appointment(
            customer_b, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(customer_user)
        response = client.post(f'/api/bookings/{appt.pk}/cancel/')
        assert response.status_code in (403, 404)


@pytest.mark.django_db
class TestBarberAppointments:
    """Tests for barber appointment management."""

    def _create_appointment(self, customer, barber, service, date, start_time, status='CONFIRMED'):
        appt = Appointment.objects.create(
            customer=customer,
            barber=barber,
            date=date,
            start_time=start_time,
            end_time=(
                datetime.datetime.combine(date, start_time)
                + datetime.timedelta(minutes=service.duration_minutes)
            ).time(),
            status=status,
            payment_method='AT_SHOP',
            payment_status='PENDING',
            total_price=service.price,
            total_duration=service.duration_minutes,
        )
        AppointmentService.objects.create(
            appointment=appt,
            service=service,
            service_name=service.name,
            service_price=service.price,
            service_duration=service.duration_minutes,
        )
        return appt

    def _next_monday(self):
        today = datetime.date.today()
        return today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)

    def test_barber_day_list(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(barber_with_schedule)
        response = client.get('/api/bookings/barber/day/')
        assert response.status_code == 200

    def test_barber_day_list_date_filter(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(barber_with_schedule)
        response = client.get(
            '/api/bookings/barber/day/',
            {'date': monday.isoformat()},
        )
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_barber_cancel(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        appt = self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(barber_with_schedule)
        response = client.post(f'/api/bookings/{appt.pk}/cancel/')
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == 'CANCELLED'

    def test_barber_no_show(
        self, auth_client, customer_user, barber_with_schedule, service_fixture,
    ):
        monday = self._next_monday()
        appt = self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            monday, datetime.time(10, 0),
        )
        client = auth_client(barber_with_schedule)
        response = client.post(f'/api/bookings/{appt.pk}/no-show/')
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == 'NO_SHOW'

    def test_auto_complete_past_appointments(
        self, customer_user, barber_with_schedule, service_fixture,
    ):
        """Management command marks past CONFIRMED -> COMPLETED."""
        from django.core.management import call_command

        past_date = datetime.date(2025, 1, 6)
        appt = self._create_appointment(
            customer_user, barber_with_schedule, service_fixture,
            past_date, datetime.time(10, 0), status='CONFIRMED',
        )
        call_command('auto_complete_appointments')
        appt.refresh_from_db()
        assert appt.status == 'COMPLETED'
