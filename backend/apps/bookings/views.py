import datetime

import stripe
from django.conf import settings as django_settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
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
    """Read-only service list for customers (the main /api/services/ requires IsBarber)."""

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
            barber = CustomUser.objects.get(pk=barber_id, role=CustomUser.Role.BARBER)
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        barber_id = request.query_params.get('barber_id')
        date_str = request.query_params.get('date')
        service_ids_str = request.query_params.get('service_ids', '')

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

        today = timezone.localdate()
        if target_date < today:
            return Response({'slots': []})

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
            duration_minutes = 30  # default if no services picked

        day_of_week = target_date.weekday()
        try:
            schedule = WeeklySchedule.objects.get(barber_id=barber_id, day_of_week=day_of_week)
        except WeeklySchedule.DoesNotExist:
            return Response({'slots': []})

        if not schedule.is_working:
            return Response({'slots': []})

        date_blocks = DateBlock.objects.filter(barber_id=barber_id, date=target_date)

        # full-day block = both start/end null
        for block in date_blocks:
            if block.block_start is None and block.block_end is None:
                return Response({'slots': []})

        block_ranges = [
            (b.block_start, b.block_end)
            for b in date_blocks
            if b.block_start is not None and b.block_end is not None
        ]

        booked = Appointment.objects.filter(
            barber_id=barber_id,
            date=target_date,
            status=Appointment.Status.CONFIRMED,
        ).values_list('start_time', 'end_time')
        booked_ranges = list(booked)

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

        # for today, skip slots less than 30min from now
        if target_date == today:
            now_plus_30 = (timezone.localtime() + datetime.timedelta(minutes=30)).time()
            slots = [
                s for s in slots
                if datetime.time.fromisoformat(s) >= now_plus_30
            ]

        return Response({'slots': slots})


class BookingCreateView(APIView):
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

        try:
            barber = CustomUser.objects.get(pk=barber_id, role=CustomUser.Role.BARBER)
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'Barber not found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        services = list(Service.objects.filter(pk__in=service_ids, barber=barber))
        if len(services) != len(service_ids):
            return Response(
                {'detail': 'One or more services not found for this barber.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_duration = sum(s.duration_minutes for s in services)
        total_price = sum(s.price for s in services)
        end_time = (
            datetime.datetime.combine(target_date, start_time)
            + datetime.timedelta(minutes=total_duration)
        ).time()

        if payment_method == 'ONLINE' and card_number.endswith('0000'):
            return Response(
                {'detail': 'Payment declined.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_method == 'ONLINE':
            payment_status = Appointment.PaymentStatus.PAID
        else:
            payment_status = Appointment.PaymentStatus.PENDING

        # lock rows to prevent double-booking
        with transaction.atomic():
            existing = list(
                Appointment.objects.select_for_update().filter(
                    barber=barber,
                    date=target_date,
                    status=Appointment.Status.CONFIRMED,
                )
            )

            for appt in existing:
                if _overlaps(start_time, end_time, appt.start_time, appt.end_time):
                    return Response(
                        {'detail': 'This time slot is already booked.'},
                        status=status.HTTP_409_CONFLICT,
                    )

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
            from apps.reviews.models import Review
            qs = Appointment.objects.filter(
                customer=request.user,
            ).filter(
                Q(status__in=[
                    Appointment.Status.COMPLETED,
                    Appointment.Status.CANCELLED,
                    Appointment.Status.NO_SHOW,
                ]) | Q(status=Appointment.Status.CONFIRMED, date__lt=today)
            ).annotate(
                has_review=Exists(Review.objects.filter(appointment=OuterRef('pk')))
            ).order_by('-date', '-start_time')

        return Response(AppointmentListSerializer(qs, many=True).data)


class BarberAppointmentListView(APIView):
    permission_classes = [IsBarber]

    def get(self, request):
        now = timezone.localtime()
        today = now.date()

        # auto-complete past appointments
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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response(
                {'detail': 'Appointment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

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


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    UZS_TO_USD_RATE = 12800

    def post(self, request):
        amount = request.data.get('amount')
        description = request.data.get('description', 'Barbershop appointment')
        if not amount or not isinstance(amount, int) or amount <= 0:
            return Response({'detail': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        stripe.api_key = django_settings.STRIPE_SECRET_KEY
        if not stripe.api_key:
            return Response({'detail': 'Stripe not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # UZS not supported by Stripe, convert to USD cents (min 50c)
        amount_usd_cents = max(50, round(amount / self.UZS_TO_USD_RATE * 100))

        frontend_url = getattr(django_settings, 'FRONTEND_URL', 'http://localhost:5173')

        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': description,
                        },
                        'unit_amount': amount_usd_cents,
                    },
                    'quantity': 1,
                }],
                metadata={
                    'user_id': request.user.id,
                    'amount_uzs': amount,
                },
                success_url=f'{frontend_url}/customer/appointments?payment=success',
                cancel_url=f'{frontend_url}/customer/appointments?payment=cancelled',
            )
            return Response({'url': session.url})
        except stripe.error.StripeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
