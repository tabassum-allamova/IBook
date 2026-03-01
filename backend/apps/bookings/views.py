"""
Booking API views.

Provides endpoints for slot availability, booking creation, appointment management,
and a customer-facing barber services read endpoint.
"""

import datetime

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, AppointmentService
from apps.bookings.serializers import (
    AppointmentListSerializer,
    AppointmentSerializer,
    BookingCreateSerializer,
)
from apps.bookings.slot_utils import _overlaps, compute_available_slots
from apps.services.models import DateBlock, Service, WeeklySchedule
from apps.users.models import CustomUser
from apps.users.permissions import IsBarber, IsCustomer


class BarberServicesPublicView(APIView):
    """
    GET /api/bookings/barber-services/?barber_id=X

    Returns a barber's service catalog for customers (read-only).
    Phase 2's /api/services/ uses IsBarber permission, so customers need
    this alternative endpoint to see services during booking.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        barber_id = request.query_params.get('barber_id')
        if not barber_id:
            return Response(
                {'detail': 'barber_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barber_id = int(barber_id)
            barber = CustomUser.objects.get(pk=barber_id, role='BARBER')
        except (ValueError, CustomUser.DoesNotExist):
            return Response(
                {'detail': 'Barber not found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        services = Service.objects.filter(barber_id=barber_id).order_by('sort_order')
        data = [
            {
                'id': s.id,
                'name': s.name,
                'price': s.price,
                'duration_minutes': s.duration_minutes,
            }
            for s in services
        ]
        return Response(data)


class AvailableSlotsView(APIView):
    """
    GET /api/bookings/slots/?barber_id=X&date=YYYY-MM-DD&service_ids=1,2,3

    Returns available time slots for a barber on a given date.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        barber_id = request.query_params.get('barber_id')
        date_str = request.query_params.get('date')
        service_ids_str = request.query_params.get('service_ids', '')

        # Validate required params
        if not barber_id or not date_str:
            return Response(
                {'detail': 'barber_id and date query parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barber_id = int(barber_id)
            target_date = datetime.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Invalid barber_id or date format.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject past dates
        today = timezone.localdate()
        if target_date < today:
            return Response({'slots': []})

        # Parse service_ids and compute total duration
        service_ids = []
        if service_ids_str:
            try:
                service_ids = [int(sid.strip()) for sid in service_ids_str.split(',') if sid.strip()]
            except ValueError:
                return Response(
                    {'detail': 'Invalid service_ids format.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if service_ids:
            services = Service.objects.filter(pk__in=service_ids, barber_id=barber_id)
            duration_minutes = sum(s.duration_minutes for s in services)
        else:
            duration_minutes = 30  # Default duration if no services specified

        # Fetch schedule for the day of week (Monday=0)
        day_of_week = target_date.weekday()
        try:
            schedule = WeeklySchedule.objects.get(barber_id=barber_id, day_of_week=day_of_week)
        except WeeklySchedule.DoesNotExist:
            return Response({'slots': []})

        if not schedule.is_working:
            return Response({'slots': []})

        # Check date blocks
        date_blocks = DateBlock.objects.filter(barber_id=barber_id, date=target_date)

        # Full-day block: block_start and block_end are both null
        for block in date_blocks:
            if block.block_start is None and block.block_end is None:
                return Response({'slots': []})

        block_ranges = [
            (b.block_start, b.block_end)
            for b in date_blocks
            if b.block_start is not None and b.block_end is not None
        ]

        # Fetch existing CONFIRMED appointments as booked ranges
        booked = Appointment.objects.filter(
            barber_id=barber_id,
            date=target_date,
            status=Appointment.Status.CONFIRMED,
        ).values_list('start_time', 'end_time')
        booked_ranges = list(booked)

        # Compute slots
        slots = compute_available_slots(
            schedule_start=schedule.start_time,
            schedule_end=schedule.end_time,
            break_start=schedule.break_start,
            break_end=schedule.break_end,
            is_working=schedule.is_working,
            block_ranges=block_ranges,
            booked_ranges=booked_ranges,
            duration_minutes=duration_minutes,
        )

        # For today: filter out slots where start_time < now + 30 minutes
        if target_date == today:
            now_plus_30 = (timezone.localtime() + datetime.timedelta(minutes=30)).time()
            slots = [
                s for s in slots
                if datetime.time.fromisoformat(s) >= now_plus_30
            ]

        return Response({'slots': slots})


class BookingCreateView(APIView):
    """
    POST /api/bookings/

    Creates a new appointment with race-condition-safe slot reservation.
    Uses transaction.atomic() + select_for_update() to prevent double-booking.
    """

    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        barber_id = data['barber_id']
        target_date = data['date']
        start_time = data['start_time']
        service_ids = data['service_ids']
        payment_method = data['payment_method']
        card_number = data.get('card_number', '')

        # Validate barber exists
        try:
            barber = CustomUser.objects.get(pk=barber_id, role='BARBER')
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'Barber not found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch services and verify they belong to this barber
        services = list(Service.objects.filter(pk__in=service_ids, barber=barber))
        if len(services) != len(service_ids):
            return Response(
                {'detail': 'One or more services not found for this barber.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Compute totals
        total_duration = sum(s.duration_minutes for s in services)
        total_price = sum(s.price for s in services)
        end_time = (
            datetime.datetime.combine(target_date, start_time)
            + datetime.timedelta(minutes=total_duration)
        ).time()

        # Handle payment
        if payment_method == 'ONLINE' and card_number.endswith('0000'):
            return Response(
                {'detail': 'Payment declined.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_method == 'ONLINE':
            payment_status = Appointment.PaymentStatus.PAID
        else:
            payment_status = Appointment.PaymentStatus.PENDING

        # Atomic booking with lock
        with transaction.atomic():
            # Lock all CONFIRMED appointments for this barber+date
            existing = list(
                Appointment.objects.select_for_update().filter(
                    barber=barber,
                    date=target_date,
                    status=Appointment.Status.CONFIRMED,
                )
            )

            # Check for overlaps
            for appt in existing:
                if _overlaps(start_time, end_time, appt.start_time, appt.end_time):
                    return Response(
                        {'detail': 'This time slot is already booked.'},
                        status=status.HTTP_409_CONFLICT,
                    )

            # Create appointment
            appointment = Appointment.objects.create(
                customer=request.user,
                barber=barber,
                date=target_date,
                start_time=start_time,
                end_time=end_time,
                status=Appointment.Status.CONFIRMED,
                payment_method=payment_method,
                payment_status=payment_status,
                total_price=total_price,
                total_duration=total_duration,
            )

            # Create service snapshots
            for svc in services:
                AppointmentService.objects.create(
                    appointment=appointment,
                    service=svc,
                    service_name=svc.name,
                    service_price=svc.price,
                    service_duration=svc.duration_minutes,
                )

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerAppointmentListView(APIView):
    """
    GET /api/bookings/my/upcoming/  — upcoming confirmed appointments
    GET /api/bookings/my/past/      — past / completed / cancelled appointments

    Separated into two URL paths for clarity.
    """

    permission_classes = [IsCustomer]

    def get(self, request, filter_type='upcoming'):
        today = timezone.localdate()

        if filter_type == 'upcoming':
            qs = Appointment.objects.filter(
                customer=request.user,
                status=Appointment.Status.CONFIRMED,
                date__gte=today,
            ).order_by('date', 'start_time')
        else:
            # Past: completed, cancelled, no-show, or past-date confirmed
            qs = Appointment.objects.filter(
                customer=request.user,
            ).filter(
                Q(status__in=[
                    Appointment.Status.COMPLETED,
                    Appointment.Status.CANCELLED,
                    Appointment.Status.NO_SHOW,
                ]) | Q(status=Appointment.Status.CONFIRMED, date__lt=today)
            ).order_by('-date', '-start_time')

        return Response(AppointmentListSerializer(qs, many=True).data)


class BarberAppointmentListView(APIView):
    """
    GET /api/bookings/barber/day/?date=YYYY-MM-DD

    Returns appointments for the authenticated barber on a given date.
    Also auto-completes past-due confirmed appointments inline.
    """

    permission_classes = [IsBarber]

    def get(self, request):
        now = timezone.localtime()
        today = now.date()

        # Inline auto-complete: mark past confirmed -> completed
        Appointment.objects.filter(
            barber=request.user,
            status=Appointment.Status.CONFIRMED,
            date__lt=today,
        ).update(status=Appointment.Status.COMPLETED)

        Appointment.objects.filter(
            barber=request.user,
            status=Appointment.Status.CONFIRMED,
            date=today,
            end_time__lte=now.time(),
        ).update(status=Appointment.Status.COMPLETED)

        # Parse date filter
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except (ValueError, TypeError):
                return Response(
                    {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = today

        qs = Appointment.objects.filter(
            barber=request.user,
            date=target_date,
        ).order_by('start_time')

        return Response(AppointmentListSerializer(qs, many=True).data)


class AppointmentCancelView(APIView):
    """
    POST /api/bookings/<pk>/cancel/

    Cancels an appointment. Both customer and barber of the appointment can cancel.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response(
                {'detail': 'Appointment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check authorization: only customer or barber of this appointment
        if request.user != appointment.customer and request.user != appointment.barber:
            return Response(
                {'detail': 'You do not have permission to cancel this appointment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {'detail': 'Only confirmed appointments can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.save()

        return Response(AppointmentSerializer(appointment).data)


class AppointmentNoShowView(APIView):
    """
    POST /api/bookings/<pk>/no-show/

    Marks an appointment as no-show. Only the barber of the appointment can do this.
    """

    permission_classes = [IsBarber]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response(
                {'detail': 'Appointment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user != appointment.barber:
            return Response(
                {'detail': 'You can only mark your own appointments as no-show.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {'detail': 'Only confirmed appointments can be marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.NO_SHOW
        appointment.save()

        return Response(AppointmentSerializer(appointment).data)
