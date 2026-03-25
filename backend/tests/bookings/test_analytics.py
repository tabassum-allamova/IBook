"""
Analytics endpoint tests.

Tests for BarberAnalyticsView and OwnerAnalyticsView.
Covers ANLT-01 (barber analytics), ANLT-02 (owner analytics), ANLT-03 (period filter).
"""

import pytest
from datetime import date, timedelta

from apps.bookings.models import Appointment, AppointmentService


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analytics_data(db, barber_with_schedule, customer_user, service_fixture):
    """
    Creates 3 COMPLETED appointments for the barber:
      - today               price=50_000   service='Haircut'
      - 5 days ago          price=80_000   service='Beard Trim'
      - 40 days ago         price=30_000   service='Haircut'

    Provides enough data to test period filtering (7d, 30d, all) and trend grouping.
    """
    today = date.today()
    barber = barber_with_schedule

    appts = []
    for days_ago, price, svc_name in [
        (0, 50_000, 'Haircut'),
        (5, 80_000, 'Beard Trim'),
        (40, 30_000, 'Haircut'),
    ]:
        appt = Appointment.objects.create(
            customer=customer_user,
            barber=barber,
            date=today - timedelta(days=days_ago),
            start_time='10:00',
            end_time='10:30',
            status=Appointment.Status.COMPLETED,
            payment_method=Appointment.PaymentMethod.AT_SHOP,
            payment_status=Appointment.PaymentStatus.PAID,
            total_price=price,
            total_duration=30,
        )
        AppointmentService.objects.create(
            appointment=appt,
            service_name=svc_name,
            service_price=price,
            service_duration=30,
        )
        appts.append(appt)

    return barber, appts


# ---------------------------------------------------------------------------
# TestBarberAnalytics
# ---------------------------------------------------------------------------


class TestBarberAnalytics:
    URL = '/api/bookings/analytics/barber/'

    def test_basic_totals(self, auth_client, analytics_data):
        """All 3 COMPLETED appointments with period=all returns correct totals."""
        barber, _ = analytics_data
        client = auth_client(barber)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        data = response.json()
        assert data['total_bookings'] == 3
        assert data['total_revenue'] == 50_000 + 80_000 + 30_000  # 160_000

    def test_period_filter(self, auth_client, analytics_data):
        """period=7d excludes the 40-day-old appointment — only 2 recent ones count."""
        barber, _ = analytics_data
        client = auth_client(barber)
        response = client.get(self.URL, {'period': '7d'})

        assert response.status_code == 200
        data = response.json()
        assert data['total_bookings'] == 2
        assert data['total_revenue'] == 50_000 + 80_000  # 130_000

    def test_trend(self, auth_client, analytics_data):
        """period=all returns a trend array; each entry has day (str), count, revenue."""
        barber, _ = analytics_data
        client = auth_client(barber)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        trend = response.json()['trend']
        assert isinstance(trend, list)
        assert len(trend) > 0
        entry = trend[0]
        assert isinstance(entry['day'], str)  # ISO date string, not date object
        assert 'count' in entry
        assert 'revenue' in entry

    def test_top_services(self, auth_client, analytics_data):
        """top_services array returned with service_name and count; sorted by count desc."""
        barber, _ = analytics_data
        client = auth_client(barber)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        top_services = response.json()['top_services']
        assert isinstance(top_services, list)
        assert len(top_services) > 0
        # 'Haircut' appears twice, 'Beard Trim' once — Haircut should be first
        assert top_services[0]['service_name'] == 'Haircut'
        assert top_services[0]['count'] == 2
        assert 'service_name' in top_services[0]

    def test_ratings_summary(self, auth_client, analytics_data):
        """ratings_summary contains avg and count; avg reflects actual review."""
        barber, appts = analytics_data
        client = auth_client(barber)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        rs = response.json()['ratings_summary']
        assert 'avg' in rs
        assert 'count' in rs
        # No reviews exist yet — count should be 0, avg None
        assert rs['count'] == 0
        assert rs['avg'] is None

    def test_empty(self, auth_client, barber_with_schedule):
        """Barber with no appointments returns zero totals and empty arrays."""
        client = auth_client(barber_with_schedule)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        data = response.json()
        assert data['total_bookings'] == 0
        assert data['total_revenue'] == 0
        assert data['trend'] == []
        assert data['top_services'] == []


# ---------------------------------------------------------------------------
# TestOwnerAnalytics
# ---------------------------------------------------------------------------


class TestOwnerAnalytics:
    URL = '/api/bookings/analytics/owner/'

    def test_owner_totals(self, auth_client, shop_owner_user, analytics_data):
        """Shop owner sees shop-wide total_bookings and total_revenue."""
        barber, _ = analytics_data
        client = auth_client(shop_owner_user)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        data = response.json()
        assert data['total_bookings'] == 3
        assert data['total_revenue'] == 160_000

    def test_barber_breakdown(self, auth_client, shop_owner_user, analytics_data):
        """Response includes barbers array with name, bookings, revenue for each barber."""
        barber, _ = analytics_data
        client = auth_client(shop_owner_user)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        barbers = response.json()['barbers']
        assert isinstance(barbers, list)
        assert len(barbers) == 1
        entry = barbers[0]
        assert 'name' in entry
        assert 'bookings' in entry
        assert 'revenue' in entry
        assert entry['bookings'] == 3
        assert entry['revenue'] == 160_000

    def test_owner_trend(self, auth_client, shop_owner_user, analytics_data):
        """Owner analytics returns a trend array with date-bucketed entries."""
        barber, _ = analytics_data
        client = auth_client(shop_owner_user)
        response = client.get(self.URL, {'period': 'all'})

        assert response.status_code == 200
        trend = response.json()['trend']
        assert isinstance(trend, list)
        assert len(trend) > 0

    def test_non_owner_rejected(self, auth_client, barber_user):
        """A barber calling the owner endpoint receives 403 Forbidden."""
        client = auth_client(barber_user)
        response = client.get(self.URL)

        assert response.status_code == 403
