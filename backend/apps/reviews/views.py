"""
Reviews API views.

ReviewCreateView      — POST /api/reviews/
BarberReviewListView  — GET  /api/reviews/barber/<int:pk>/
"""

from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment
from apps.reviews.models import Review, ReviewService
from apps.reviews.serializers import ReviewCreateSerializer, ReviewListItemSerializer
from apps.users.permissions import IsCustomer


class ReviewCreateView(APIView):
    """
    POST /api/reviews/

    Creates a review for a completed appointment owned by the authenticated customer.
    Returns 404 if appointment not found, not completed, or not owned by the customer.
    Returns 400 if a review already exists for that appointment.
    """

    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Look up appointment: must belong to this customer and be COMPLETED
        try:
            appointment = Appointment.objects.select_related('barber').get(
                pk=data['appointment_id'],
                customer=request.user,
                status=Appointment.Status.COMPLETED,
            )
        except Appointment.DoesNotExist:
            return Response(
                {'detail': 'Appointment not found or not eligible for review.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Enforce one review per appointment
        if hasattr(appointment, 'review'):
            return Response(
                {'detail': 'Review already submitted for this appointment.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create review
        review = Review.objects.create(
            appointment=appointment,
            reviewer=request.user,
            barber=appointment.barber,
            rating=data['rating'],
            text=data.get('text', ''),
        )

        # Create per-service ratings if provided
        for svc in data.get('service_ratings', []):
            service_name = svc.get('service_name', '')
            svc_rating = svc.get('rating')
            if service_name and svc_rating:
                ReviewService.objects.create(
                    review=review,
                    service_name=service_name,
                    rating=int(svc_rating),
                )

        return Response({'id': review.id}, status=status.HTTP_201_CREATED)


class BarberReviewListView(APIView):
    """
    GET /api/reviews/barber/<int:pk>/

    Returns aggregated review stats and recent reviews for a barber.
    Response shape:
    {
        avg_rating: float | null,
        total_reviews: int,
        distribution: {5: N, 4: N, 3: N, 2: N, 1: N},
        recent_reviews: [{reviewer, rating, text, date}, ...]
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        qs = Review.objects.filter(barber_id=pk).select_related('reviewer')

        # Aggregate stats
        agg = qs.aggregate(
            avg=Avg('rating'),
            total=Count('id'),
            count_5=Count('id', filter=Q(rating=5)),
            count_4=Count('id', filter=Q(rating=4)),
            count_3=Count('id', filter=Q(rating=3)),
            count_2=Count('id', filter=Q(rating=2)),
            count_1=Count('id', filter=Q(rating=1)),
        )

        avg_rating = round(float(agg['avg']), 1) if agg['avg'] else None

        recent = qs.order_by('-created_at')[:10]
        recent_data = ReviewListItemSerializer(recent, many=True).data

        return Response({
            'avg_rating': avg_rating,
            'total_reviews': agg['total'],
            'distribution': {
                5: agg['count_5'],
                4: agg['count_4'],
                3: agg['count_3'],
                2: agg['count_2'],
                1: agg['count_1'],
            },
            'recent_reviews': recent_data,
        })
