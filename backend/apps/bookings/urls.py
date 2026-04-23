from django.urls import path

from apps.bookings.analytics_views import BarberAnalyticsView, OwnerAnalyticsView
from apps.bookings.views import (
    AppointmentCancelView,
    AppointmentDetailView,
    AppointmentNoShowView,
    AppointmentRescheduleView,
    AvailableSlotsView,
    BarberAppointmentListView,
    BarberServicesPublicView,
    BookingCreateView,
    CreateCheckoutSessionView,
    CustomerAppointmentListView,
    FinalizeCheckoutSessionView,
    StripeWebhookView,
)

urlpatterns = [
    path('barber-services/', BarberServicesPublicView.as_view(), name='barber-services-public'),
    path('slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('analytics/barber/', BarberAnalyticsView.as_view(), name='barber-analytics'),
    path('analytics/owner/', OwnerAnalyticsView.as_view(), name='owner-analytics'),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('finalize-checkout-session/', FinalizeCheckoutSessionView.as_view(), name='finalize-checkout-session'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', BookingCreateView.as_view(), name='booking-create'),
    path('my/upcoming/', CustomerAppointmentListView.as_view(),
         {'filter_type': 'upcoming'}, name='customer-appointments-upcoming'),
    path('my/past/', CustomerAppointmentListView.as_view(),
         {'filter_type': 'past'}, name='customer-appointments-past'),
    path('barber/day/', BarberAppointmentListView.as_view(), name='barber-appointments-day'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('<int:pk>/reschedule/', AppointmentRescheduleView.as_view(), name='appointment-reschedule'),
    path('<int:pk>/no-show/', AppointmentNoShowView.as_view(), name='appointment-no-show'),
]
