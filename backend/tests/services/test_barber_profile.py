"""
BARB-01: Barber profile photo upload tests — Wave 0 stubs (RED).

These tests will fail until Plan 02-03 implements avatar upload on the profile endpoint.
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _make_test_image(filename='avatar.png'):
    """Create a minimal 1x1 PNG for upload testing."""
    img = Image.new('RGB', (1, 1), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return SimpleUploadedFile(filename, buf.getvalue(), content_type='image/png')


@pytest.mark.django_db
def test_barber_photo_upload(auth_client, barber_user):
    """Barber can PATCH /api/auth/profile/ with avatar FormData → 200 with avatar URL."""
    client = auth_client(barber_user)
    avatar = _make_test_image()
    response = client.patch(
        '/api/auth/profile/',
        {'avatar': avatar},
        format='multipart',
    )
    assert response.status_code == 200
    assert 'avatar' in response.data
    assert response.data['avatar'] is not None
