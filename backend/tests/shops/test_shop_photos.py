"""
SHOP-01: Shop photo upload tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-02 implements ShopPhoto model + upload endpoint.
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _make_test_image(filename='photo.png'):
    """Create a minimal 1x1 PNG for upload testing."""
    img = Image.new('RGB', (1, 1), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return SimpleUploadedFile(filename, buf.getvalue(), content_type='image/png')


@pytest.mark.django_db
def test_upload_shop_photo(auth_client, shop_owner_user, shop_fixture):
    """Shop owner can POST an image to /api/shops/{id}/photos/ and get 201."""
    client = auth_client(shop_owner_user)
    photo = _make_test_image()
    response = client.post(
        f'/api/shops/{shop_fixture.id}/photos/',
        {'image': photo},
        format='multipart',
    )
    assert response.status_code == 201
