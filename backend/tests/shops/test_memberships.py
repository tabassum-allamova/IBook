"""
SHOP-02: Shop membership (barber assignment) tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-02 implements the ShopMembership model + endpoints.
"""

import pytest


@pytest.mark.django_db
def test_owner_adds_barber(auth_client, shop_owner_user, barber_user, shop_fixture):
    """Shop owner can POST /api/shops/{id}/members/ with barber_id → 201."""
    client = auth_client(shop_owner_user)
    response = client.post(
        f'/api/shops/{shop_fixture.id}/members/',
        {'barber_id': barber_user.id},
        format='json',
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_owner_removes_barber(auth_client, shop_owner_user, barber_user, shop_fixture):
    """Shop owner can DELETE /api/shops/{id}/members/{barber_id}/ → 204."""
    client = auth_client(shop_owner_user)
    response = client.delete(
        f'/api/shops/{shop_fixture.id}/members/{barber_user.id}/',
    )
    assert response.status_code == 204


@pytest.mark.django_db
def test_owner_cannot_add_to_other_shop(auth_client, shop_owner_user, barber_user, shop_fixture):
    """Shop owner cannot add barbers to a shop they don't own → 403 or 404."""
    client = auth_client(shop_owner_user)
    other_shop_id = shop_fixture.id + 9999
    response = client.post(
        f'/api/shops/{other_shop_id}/members/',
        {'barber_id': barber_user.id},
        format='json',
    )
    assert response.status_code in (403, 404)
