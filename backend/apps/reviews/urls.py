from django.urls import path

from apps.reviews.views import BarberReviewListView, ReviewCreateView

urlpatterns = [
    path('', ReviewCreateView.as_view(), name='review-create'),
    path('barber/<int:pk>/', BarberReviewListView.as_view(), name='barber-reviews'),
]
