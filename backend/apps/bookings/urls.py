"""
Booking URL configuration.

All endpoints live at /api/bookings/* (included from config/urls.py).
"""

from django.urls import path

from apps.bookings.views import (
    AppointmentCancelView,
    AppointmentNoShowView,
    AvailableSlotsView,
    BarberAppointmentListView,
    BarberServicesPublicView,
    BookingCreateView,
    CustomerAppointmentListView,
)

urlpatterns = [
    # Customer-facing barber services read endpoint
    path('barber-services/', BarberServicesPublicView.as_view(), name='barber-services-public'),

    # Slot availability
    path('slots/', AvailableSlotsView.as_view(), name='available-slots'),

    # Booking creation
    path('', BookingCreateView.as_view(), name='booking-create'),

    # Customer appointment lists
    path('my/upcoming/', CustomerAppointmentListView.as_view(),
         {'filter_type': 'upcoming'}, name='customer-appointments-upcoming'),
    path('my/past/', CustomerAppointmentListView.as_view(),
         {'filter_type': 'past'}, name='customer-appointments-past'),

    # Barber appointment list (by day)
    path('barber/day/', BarberAppointmentListView.as_view(), name='barber-appointments-day'),

    # Appointment actions
    path('<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('<int:pk>/no-show/', AppointmentNoShowView.as_view(), name='appointment-no-show'),
]
