"""
Tests for the barber profile detail endpoint (DISC-03).

Covers:
- GET /api/barbers/<id>/ returns barber full profile (name, avatar, bio, services, schedule, shop_name, avg_rating)
- GET /api/barbers/<customer_id>/ returns 404 (non-barber)
- GET /api/barbers/99999/ returns 404 (nonexistent)
- Customer user can access barber profiles (not restricted)
- Services in response are ordered by sort_order
"""

import pytest
from apps.users.models import CustomUser
from apps.shops.models import BarberShopMembership
from apps.services.models import Service, WeeklySchedule


# ---------------------------------------------------------------------------
# Additional fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def barber_full_profile(db, barber_user, shop_fixture):
    """Barber with bio, experience, shop membership, services, and full weekly schedule."""
    # Update barber profile fields
    barber_user.first_name = "Ahmed"
    barber_user.last_name = "Karimov"
    barber_user.bio = "Professional barber with 5 years of experience."
    barber_user.years_of_experience = 5
    barber_user.save()

    # Add shop membership
    BarberShopMembership.objects.create(shop=shop_fixture, barber=barber_user)

    # Add services with explicit sort_order
    Service.objects.create(barber=barber_user, name="Beard Trim", price=30000, duration_minutes=20, sort_order=2)
    Service.objects.create(barber=barber_user, name="Haircut", price=50000, duration_minutes=30, sort_order=1)
    Service.objects.create(barber=barber_user, name="Full Package", price=80000, duration_minutes=60, sort_order=3)

    # Create full 7-day weekly schedule
    for day in range(5):  # Mon-Fri working
        WeeklySchedule.objects.create(
            barber=barber_user,
            day_of_week=day,
            is_working=True,
            start_time="09:00",
            end_time="18:00",
        )
    for day in range(5, 7):  # Sat-Sun off
        WeeklySchedule.objects.create(
            barber=barber_user,
            day_of_week=day,
            is_working=False,
        )

    return barber_user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_barber_profile_returns_full_data(auth_client, customer_user, barber_full_profile):
    """
    GET /api/barbers/<id>/ returns barber full_name, avatar, bio, years_of_experience,
    services list, weekly_schedule (7 entries), shop_name, avg_rating (null).
    """
    client = auth_client(customer_user)
    response = client.get(f"/api/barbers/{barber_full_profile.pk}/")

    assert response.status_code == 200
    data = response.json()

    # Identity fields
    assert data["id"] == barber_full_profile.pk
    assert data["full_name"] == "Ahmed Karimov"
    assert data["bio"] == "Professional barber with 5 years of experience."
    assert data["years_of_experience"] == 5

    # Services list (3 services)
    assert "services" in data
    assert len(data["services"]) == 3

    # Each service has required fields
    for svc in data["services"]:
        assert "id" in svc
        assert "name" in svc
        assert "price" in svc
        assert "duration_minutes" in svc

    # Weekly schedule (7 entries)
    assert "weekly_schedule" in data
    assert len(data["weekly_schedule"]) == 7

    # Each schedule entry has required fields
    for entry in data["weekly_schedule"]:
        assert "day_of_week" in entry
        assert "is_working" in entry

    # Shop name populated from membership
    assert data["shop_name"] == "Test Barbershop"

    # avg_rating is null (Phase 5 placeholder)
    assert data["avg_rating"] is None


@pytest.mark.django_db
def test_barber_profile_404_non_barber(auth_client, customer_user):
    """GET /api/barbers/<customer_id>/ returns 404 (non-barber user)."""
    client = auth_client(customer_user)
    response = client.get(f"/api/barbers/{customer_user.pk}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_barber_profile_404_nonexistent(auth_client, customer_user):
    """GET /api/barbers/99999/ returns 404 (nonexistent user)."""
    client = auth_client(customer_user)
    response = client.get("/api/barbers/99999/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_barber_profile_accessible_by_customer(auth_client, customer_user, barber_full_profile):
    """Customer user can access any barber's profile — not restricted to barber role."""
    client = auth_client(customer_user)
    response = client.get(f"/api/barbers/{barber_full_profile.pk}/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == barber_full_profile.pk


@pytest.mark.django_db
def test_barber_profile_services_ordered(auth_client, customer_user, barber_full_profile):
    """Services in response are ordered by sort_order ascending."""
    client = auth_client(customer_user)
    response = client.get(f"/api/barbers/{barber_full_profile.pk}/")

    assert response.status_code == 200
    data = response.json()

    services = data["services"]
    sort_orders_from_name = {
        "Haircut": 1,
        "Beard Trim": 2,
        "Full Package": 3,
    }
    # Verify services are returned in sort_order order (Haircut=1, Beard Trim=2, Full Package=3)
    names = [s["name"] for s in services]
    assert names == ["Haircut", "Beard Trim", "Full Package"], (
        f"Expected services ordered by sort_order, got: {names}"
    )


@pytest.mark.django_db
def test_barber_profile_unauthenticated(api_client, barber_user):
    """GET /api/barbers/<id>/ is public — anonymous users can browse."""
    response = api_client.get(f"/api/barbers/{barber_user.pk}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_barber_profile_no_shop(auth_client, customer_user, barber_user):
    """GET /api/barbers/<id>/ for barber with no shop membership returns shop_name: null."""
    client = auth_client(customer_user)
    response = client.get(f"/api/barbers/{barber_user.pk}/")

    assert response.status_code == 200
    data = response.json()
    assert data["shop_name"] is None
