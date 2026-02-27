"""
Shared pytest fixtures for the IBook backend test suite.

Wave 0: Fixtures define users and API clients that all subsequent test waves will use.
The fixtures create real DB rows so they exercise the CustomUser model.

Phase 2 additions: shop_fixture stub — skipped until Plan 02-02 creates the Shop model.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import CustomUser


# ---------------------------------------------------------------------------
# API Client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client() -> APIClient:
    """Returns an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def auth_client(api_client: APIClient):
    """
    Factory fixture — call with a user to get an authenticated APIClient.

    Usage:
        def test_something(auth_client, customer_user):
            client = auth_client(customer_user)
            response = client.get("/api/auth/profile/")
    """

    def _auth_client(user: CustomUser) -> APIClient:
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        return api_client

    return _auth_client


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def customer_user(db) -> CustomUser:
    """Customer user — email verified, active."""
    user = CustomUser.objects.create_user(
        username="customer_test",
        email="customer@test.com",
        password="Test1234",
        role=CustomUser.Role.CUSTOMER,
        is_email_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def barber_user(db) -> CustomUser:
    """Barber user — email verified, active."""
    user = CustomUser.objects.create_user(
        username="barber_test",
        email="barber@test.com",
        password="Test1234",
        role=CustomUser.Role.BARBER,
        is_email_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def shop_owner_user(db) -> CustomUser:
    """Shop owner user — email verified, active."""
    user = CustomUser.objects.create_user(
        username="owner_test",
        email="owner@test.com",
        password="Test1234",
        role=CustomUser.Role.SHOP_OWNER,
        is_email_verified=True,
        is_active=True,
    )
    return user


# ---------------------------------------------------------------------------
# Phase 2 fixtures — shop_fixture is a stub until Plan 02-02 creates the model
# ---------------------------------------------------------------------------


@pytest.fixture
def shop_fixture(db, shop_owner_user):
    """
    Real fixture — creates a Shop row for the shop_owner_user.

    Implemented in Plan 02-02 (shops app). Replaces the stub that called pytest.skip().
    """
    from apps.shops.models import Shop

    return Shop.objects.create(
        owner=shop_owner_user,
        name='Test Barbershop',
        address='1 Main St',
        lat='41.299496',
        lng='69.240073',
        description='A fixture shop for testing',
    )


# ---------------------------------------------------------------------------
# Phase 3 fixtures — booking-related helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def barber_with_schedule(db, barber_user, shop_fixture):
    """Barber with a shop membership and Mon-Fri 09:00-18:00 schedule, break 13:00-14:00."""
    from apps.shops.models import BarberShopMembership
    from apps.services.models import WeeklySchedule

    BarberShopMembership.objects.create(shop=shop_fixture, barber=barber_user)
    for day in range(5):  # Mon-Fri
        WeeklySchedule.objects.update_or_create(
            barber=barber_user, day_of_week=day,
            defaults={
                'is_working': True,
                'start_time': '09:00',
                'end_time': '18:00',
                'break_start': '13:00',
                'break_end': '14:00',
            },
        )
    for day in range(5, 7):  # Sat-Sun off
        WeeklySchedule.objects.update_or_create(
            barber=barber_user, day_of_week=day,
            defaults={'is_working': False},
        )
    return barber_user


@pytest.fixture
def service_fixture(db, barber_user):
    """A 30-minute service at 50000 UZS for the barber_user."""
    from apps.services.models import Service

    return Service.objects.create(
        barber=barber_user,
        name='Haircut',
        price=50000,
        duration_minutes=30,
    )
