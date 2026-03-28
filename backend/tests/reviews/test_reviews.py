"""
Integration tests for the reviews API.

Covers:
  - POST /api/reviews/  (ReviewCreateView)
  - GET  /api/reviews/barber/<pk>/  (BarberReviewListView)
  - has_review annotation on GET /api/bookings/my/past/
  - Real avg_rating on GET /api/barbers/<pk>/
"""

import datetime

import pytest

from apps.bookings.models import Appointment, AppointmentService
from apps.reviews.models import Review, ReviewService
from apps.users.models import CustomUser


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_completed_appointment(customer, barber, service):
    """Create a COMPLETED appointment yesterday with an AppointmentService snapshot."""
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    appt = Appointment.objects.create(
        customer=customer,
        barber=barber,
        date=yesterday,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(10, 30),
        status=Appointment.Status.COMPLETED,
        payment_method='AT_SHOP',
        payment_status='PENDING',
        total_price=50000,
        total_duration=30,
    )
    AppointmentService.objects.create(
        appointment=appt,
        service=service,
        service_name=service.name,
        service_price=service.price,
        service_duration=service.duration_minutes,
    )
    return appt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def completed_appointment(db, customer_user, barber_user, service_fixture):
    """A completed appointment owned by customer_user with barber_user."""
    return _make_completed_appointment(customer_user, barber_user, service_fixture)


# ---------------------------------------------------------------------------
# TestReviewCreate
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestReviewCreate:

    def test_create_review_success(
        self, auth_client, customer_user, completed_appointment, service_fixture,
    ):
        """POST with valid data creates review and service rating rows, returns 201."""
        client = auth_client(customer_user)
        payload = {
            'appointment_id': completed_appointment.id,
            'rating': 5,
            'text': 'Great haircut!',
            'service_ratings': [{'service_name': 'Haircut', 'rating': 5}],
        }
        response = client.post('/api/reviews/', payload, format='json')
        assert response.status_code == 201, response.data
        assert Review.objects.count() == 1
        assert ReviewService.objects.count() == 1
        review = Review.objects.first()
        assert review.rating == 5
        assert review.text == 'Great haircut!'

    def test_not_completed(
        self, auth_client, customer_user, barber_user, service_fixture, db,
    ):
        """POST for a CONFIRMED appointment returns 404."""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        appt = Appointment.objects.create(
            customer=customer_user,
            barber=barber_user,
            date=tomorrow,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
            status=Appointment.Status.CONFIRMED,
            payment_method='AT_SHOP',
            payment_status='PENDING',
            total_price=50000,
            total_duration=30,
        )
        client = auth_client(customer_user)
        response = client.post(
            '/api/reviews/',
            {'appointment_id': appt.id, 'rating': 4},
            format='json',
        )
        assert response.status_code == 404

    def test_duplicate(
        self, auth_client, customer_user, completed_appointment,
    ):
        """POST twice for the same appointment returns 400 on second attempt."""
        client = auth_client(customer_user)
        payload = {'appointment_id': completed_appointment.id, 'rating': 5}
        r1 = client.post('/api/reviews/', payload, format='json')
        assert r1.status_code == 201
        r2 = client.post('/api/reviews/', payload, format='json')
        assert r2.status_code == 400
        assert 'already submitted' in str(r2.data).lower()

    def test_wrong_customer(
        self, auth_client, completed_appointment, db,
    ):
        """POST by a different customer returns 404."""
        other_customer = CustomUser.objects.create_user(
            username='other_customer',
            email='other@test.com',
            password='Test1234',
            role=CustomUser.Role.CUSTOMER,
            is_email_verified=True,
            is_active=True,
        )
        client = auth_client(other_customer)
        response = client.post(
            '/api/reviews/',
            {'appointment_id': completed_appointment.id, 'rating': 3},
            format='json',
        )
        assert response.status_code == 404

    def test_barber_cannot_review(
        self, auth_client, barber_user, completed_appointment,
    ):
        """Barbers are not customers; POST returns 403."""
        client = auth_client(barber_user)
        response = client.post(
            '/api/reviews/',
            {'appointment_id': completed_appointment.id, 'rating': 5},
            format='json',
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# TestBarberReviews
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBarberReviews:

    def _make_review(self, customer, barber, service, rating):
        """Create a completed appointment and review."""
        appt = _make_completed_appointment(customer, barber, service)
        return Review.objects.create(
            appointment=appt,
            reviewer=customer,
            barber=barber,
            rating=rating,
        )

    def test_list_reviews(
        self, auth_client, customer_user, barber_user, service_fixture, db,
    ):
        """GET returns avg_rating, total_reviews, distribution, and recent_reviews."""
        # Need 3 customers to make 3 reviews (one per appointment)
        c2 = CustomUser.objects.create_user(
            username='c2', email='c2@test.com', password='Test1234',
            role=CustomUser.Role.CUSTOMER, is_email_verified=True, is_active=True,
        )
        c3 = CustomUser.objects.create_user(
            username='c3', email='c3@test.com', password='Test1234',
            role=CustomUser.Role.CUSTOMER, is_email_verified=True, is_active=True,
        )
        self._make_review(customer_user, barber_user, service_fixture, 5)
        self._make_review(c2, barber_user, service_fixture, 4)
        self._make_review(c3, barber_user, service_fixture, 3)

        client = auth_client(customer_user)
        response = client.get(f'/api/reviews/barber/{barber_user.id}/')
        assert response.status_code == 200
        data = response.data
        assert isinstance(data['avg_rating'], float)
        assert data['total_reviews'] == 3
        assert 'distribution' in data
        assert data['distribution'][5] == 1
        assert data['distribution'][4] == 1
        assert data['distribution'][3] == 1
        assert len(data['recent_reviews']) == 3

    def test_empty(self, auth_client, customer_user, barber_user, db):
        """GET for barber with no reviews returns avg_rating=None, total=0."""
        client = auth_client(customer_user)
        response = client.get(f'/api/reviews/barber/{barber_user.id}/')
        assert response.status_code == 200
        assert response.data['avg_rating'] is None
        assert response.data['total_reviews'] == 0


# ---------------------------------------------------------------------------
# TestHasReviewAnnotation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHasReviewAnnotation:

    def test_past_with_review(
        self, auth_client, customer_user, barber_user, service_fixture, db,
    ):
        """Completed appointment with review → has_review=True in past list."""
        appt = _make_completed_appointment(customer_user, barber_user, service_fixture)
        Review.objects.create(
            appointment=appt,
            reviewer=customer_user,
            barber=barber_user,
            rating=5,
        )
        client = auth_client(customer_user)
        response = client.get('/api/bookings/my/past/')
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['has_review'] is True

    def test_past_without_review(
        self, auth_client, customer_user, barber_user, service_fixture, db,
    ):
        """Completed appointment without review → has_review=False in past list."""
        _make_completed_appointment(customer_user, barber_user, service_fixture)
        client = auth_client(customer_user)
        response = client.get('/api/bookings/my/past/')
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['has_review'] is False


# ---------------------------------------------------------------------------
# TestAvgRating
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAvgRating:

    def test_barber_profile_avg(
        self, auth_client, customer_user, barber_user, service_fixture, db,
    ):
        """After 2 reviews (4 and 5), barber profile avg_rating = 4.5."""
        c2 = CustomUser.objects.create_user(
            username='c_avg2', email='cavg2@test.com', password='Test1234',
            role=CustomUser.Role.CUSTOMER, is_email_verified=True, is_active=True,
        )
        appt1 = _make_completed_appointment(customer_user, barber_user, service_fixture)
        appt2 = _make_completed_appointment(c2, barber_user, service_fixture)
        Review.objects.create(
            appointment=appt1, reviewer=customer_user, barber=barber_user, rating=4,
        )
        Review.objects.create(
            appointment=appt2, reviewer=c2, barber=barber_user, rating=5,
        )
        client = auth_client(customer_user)
        response = client.get(f'/api/barbers/{barber_user.id}/')
        assert response.status_code == 200
        assert response.data['avg_rating'] == 4.5

    def test_barber_profile_no_reviews(
        self, auth_client, customer_user, barber_user, db,
    ):
        """Barber with no reviews → avg_rating is None."""
        client = auth_client(customer_user)
        response = client.get(f'/api/barbers/{barber_user.id}/')
        assert response.status_code == 200
        assert response.data['avg_rating'] is None
