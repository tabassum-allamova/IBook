"""
Tests for the shop list endpoint (DISC-01, DISC-02).

Covers:
- GET /api/shops/ with lat/lng — returns shops ordered by distance_km ascending
- GET /api/shops/ without lat/lng — returns all shops, distance_km is null
- GET /api/shops/?name=X — filters shops by name (case-insensitive partial match)
- Distance accuracy: shop at known Tashkent coords returns ~3-5km from query point
- Shops with null lat/lng excluded when coords provided
- Each shop card has required fields: id, name, address, lat, lng, photo, distance_km,
  is_open_now, min_price, avg_rating
"""

import pytest
from apps.shops.models import BarberShopMembership, Shop, ShopHours
from apps.services.models import Service
from apps.users.models import CustomUser


# ---------------------------------------------------------------------------
# Additional fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def second_shop_owner(db):
    """A second shop owner user."""
    return CustomUser.objects.create_user(
        username="owner2_test",
        email="owner2@test.com",
        password="Test1234",
        role=CustomUser.Role.SHOP_OWNER,
        is_email_verified=True,
        is_active=True,
    )


@pytest.fixture
def distant_shop(db, second_shop_owner):
    """Shop far from Tashkent center — at approximately (41.3111, 69.2797)."""
    return Shop.objects.create(
        owner=second_shop_owner,
        name="Distant Barbershop",
        address="Far away street",
        lat="41.3111",
        lng="69.2797",
        description="A distant shop",
    )


@pytest.fixture
def shop_no_coords(db, shop_owner_user):
    """Shop with null lat/lng — should be excluded from distance queries."""
    # Use a different owner to avoid OneToOne conflict with shop_fixture
    owner = CustomUser.objects.create_user(
        username="owner_null_coords",
        email="owner_null@test.com",
        password="Test1234",
        role=CustomUser.Role.SHOP_OWNER,
        is_email_verified=True,
        is_active=True,
    )
    return Shop.objects.create(
        owner=owner,
        name="No Coords Barbershop",
        address="Unknown street",
        lat=None,
        lng=None,
        description="A shop with no coordinates",
    )


@pytest.fixture
def shop_with_service(db, shop_fixture, barber_user):
    """Shop fixture with a barber member and a service."""
    BarberShopMembership.objects.create(shop=shop_fixture, barber=barber_user)
    Service.objects.create(
        barber=barber_user,
        name="Haircut",
        price=50000,
        duration_minutes=30,
    )
    return shop_fixture


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_shop_list_with_coords(auth_client, customer_user, shop_fixture, distant_shop):
    """
    GET /api/shops/?lat=41.30&lng=69.24 returns shops ordered by distance_km ascending.
    Each shop has a distance_km field.
    """
    client = auth_client(customer_user)
    response = client.get("/api/shops/", {"lat": "41.30", "lng": "69.24"})

    assert response.status_code == 200
    data = response.json()

    # Both shops should be in the result (both have valid coords)
    assert len(data) >= 2

    # All shops should have distance_km
    for shop in data:
        assert "distance_km" in shop
        assert shop["distance_km"] is not None

    # Shops should be ordered by distance ascending
    distances = [shop["distance_km"] for shop in data]
    assert distances == sorted(distances), "Shops should be ordered by distance_km ascending"


@pytest.mark.django_db
def test_shop_list_no_coords(auth_client, customer_user, shop_fixture):
    """
    GET /api/shops/ without lat/lng returns all shops.
    distance_km should be null for each shop.
    """
    client = auth_client(customer_user)
    response = client.get("/api/shops/")

    assert response.status_code == 200
    data = response.json()

    # Should have at least one shop
    assert len(data) >= 1

    # All distance_km should be null
    for shop in data:
        assert "distance_km" in shop
        assert shop["distance_km"] is None


@pytest.mark.django_db
def test_shop_list_name_filter(auth_client, customer_user, shop_fixture, distant_shop):
    """
    GET /api/shops/?name=test returns only shops whose name contains "test" (case-insensitive).
    """
    client = auth_client(customer_user)
    response = client.get("/api/shops/", {"name": "test"})

    assert response.status_code == 200
    data = response.json()

    # shop_fixture is named "Test Barbershop", should match
    assert len(data) >= 1
    for shop in data:
        assert "test" in shop["name"].lower()

    # "Distant Barbershop" does not contain "test", should not be included
    names = [s["name"] for s in data]
    assert "Distant Barbershop" not in names


@pytest.mark.django_db
def test_distance_annotation_accuracy(auth_client, customer_user, shop_fixture):
    """
    Shop at Tashkent center (41.299496, 69.240073) queried from (41.3111, 69.2797)
    should return distance in ~3-5km range (sanity check).
    """
    # shop_fixture is at lat=41.299496, lng=69.240073 (Tashkent center)
    # Query from (41.3111, 69.2797) — approximately 3-4km away
    client = auth_client(customer_user)
    response = client.get("/api/shops/", {"lat": "41.3111", "lng": "69.2797"})

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1

    # Find the shop_fixture by name
    target = next((s for s in data if s["name"] == "Test Barbershop"), None)
    assert target is not None, "Test Barbershop should be in results"
    assert target["distance_km"] is not None

    # Sanity check: distance should be between 2 and 6 km
    assert 2.0 <= target["distance_km"] <= 6.0, (
        f"Expected ~3-5km, got {target['distance_km']}km"
    )


@pytest.mark.django_db
def test_shop_list_excludes_null_coords(auth_client, customer_user, shop_fixture, shop_no_coords):
    """
    Shops with null lat/lng are excluded when lat/lng query params are provided.
    """
    client = auth_client(customer_user)
    response = client.get("/api/shops/", {"lat": "41.30", "lng": "69.24"})

    assert response.status_code == 200
    data = response.json()

    # shop_no_coords should NOT be in results
    names = [s["name"] for s in data]
    assert "No Coords Barbershop" not in names


@pytest.mark.django_db
def test_shop_list_card_fields(auth_client, customer_user, shop_fixture):
    """
    Each shop in response has fields: id, name, address, lat, lng, photo,
    distance_km, is_open_now, min_price, avg_rating.
    """
    client = auth_client(customer_user)
    response = client.get("/api/shops/")

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    shop = data[0]

    required_fields = ["id", "name", "address", "lat", "lng", "photo",
                       "distance_km", "is_open_now", "min_price", "avg_rating"]
    for field in required_fields:
        assert field in shop, f"Missing field: {field}"


@pytest.mark.django_db
def test_shop_list_unauthenticated(api_client, shop_fixture):
    """GET /api/shops/ without auth is public — anonymous users can browse."""
    response = api_client.get("/api/shops/")
    assert response.status_code == 200
