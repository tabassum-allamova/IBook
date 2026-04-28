import datetime

import stripe
from django.conf import settings as django_settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, AppointmentService
from apps.bookings.risk import CustomerStats
from apps.bookings.serializers import (
    AppointmentListSerializer,
    AppointmentSerializer,
    BookingCreateSerializer,
    RescheduleSerializer,
)
from apps.bookings.slot_utils import _overlaps, compute_available_slots
from apps.services.models import DateBlock, Service, WeeklySchedule
from apps.users.models import CustomUser
from apps.users.permissions import IsBarber, IsCustomer


# Unpaid ONLINE bookings reserve the slot for this long while the customer
# completes Stripe checkout. After this window lapses an abandoned booking
# no longer blocks the calendar (the DB row stays as a breadcrumb until the
# daily cleanup sweep cancels it).
PAYMENT_HOLD_MINUTES = 15


def _active_slot_filter(now=None):
    """Q filter: appointments that currently occupy their slot.

    CONFIRMED appointments count, *except* unpaid ONLINE ones that are older
    than the hold window — those have abandoned Stripe and the slot should
    be available again.
    """
    now = now or timezone.now()
    hold_cutoff = now - datetime.timedelta(minutes=PAYMENT_HOLD_MINUTES)
    return Q(status=Appointment.Status.CONFIRMED) & ~(
        Q(payment_method=Appointment.PaymentMethod.ONLINE)
        & Q(payment_status=Appointment.PaymentStatus.PENDING)
        & Q(created_at__lt=hold_cutoff)
    )


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

        booked_qs = Appointment.objects.filter(
            barber_id=barber_id,
            date=target_date,
        ).filter(_active_slot_filter())
        # Only honor `exclude_appointment_id` when the caller actually owns
        # (or is the barber on) that appointment. Without this check any
        # authenticated user could pass another customer's appointment ID to
        # make an occupied slot appear free and race-book it.
        exclude_id = request.query_params.get('exclude_appointment_id')
        if exclude_id:
            try:
                exclude_id_int = int(exclude_id)
            except (ValueError, TypeError):
                exclude_id_int = None
            if exclude_id_int is not None:
                owns = Appointment.objects.filter(
                    pk=exclude_id_int,
                ).filter(
                    Q(customer=request.user) | Q(barber=request.user)
                ).exists()
                if owns:
                    booked_qs = booked_qs.exclude(pk=exclude_id_int)
        booked_ranges = list(booked_qs.values_list('start_time', 'end_time'))

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

        # Online bookings start unpaid; Stripe webhook (or finalize fallback)
        # flips payment_status to PAID. Until then the slot is held for
        # PAYMENT_HOLD_MINUTES via _active_slot_filter, after which an
        # abandoned checkout no longer blocks the calendar.
        payment_status = Appointment.PaymentStatus.PENDING

        # Two-layer defence against double-booking:
        # 1. Python overlap check against active slots (fast path, gives a
        #    friendly error before the INSERT).
        # 2. Conditional UniqueConstraint on (barber, date, start_time) for
        #    status=CONFIRMED. If two requests race past the Python check
        #    the DB rejects the second INSERT with IntegrityError.
        try:
            with transaction.atomic():
                existing = list(
                    Appointment.objects.select_for_update()
                    .filter(barber=barber, date=target_date)
                    .filter(_active_slot_filter())
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
        except IntegrityError:
            return Response(
                {'detail': 'This time slot was just booked by someone else.'},
                status=status.HTTP_409_CONFLICT,
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
            # Surface both CONFIRMED and CANCELLED future bookings. A customer
            # needs to know if the barber cancelled on them so they can rebook.
            # Sort CONFIRMED first so active bookings stay at the top.
            from django.db.models import Case, IntegerField, Value, When
            qs = (
                Appointment.objects.filter(
                    customer=request.user,
                    date__gte=today,
                    status__in=[
                        Appointment.Status.CONFIRMED,
                        Appointment.Status.CANCELLED,
                    ],
                )
                .annotate(
                    _status_rank=Case(
                        When(status=Appointment.Status.CONFIRMED, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    ),
                )
                .order_by('_status_rank', 'date', 'start_time')
            )
        else:
            # Past: anything with a date in the past, plus terminal statuses.
            from apps.reviews.models import Review
            qs = Appointment.objects.filter(
                customer=request.user,
            ).filter(
                Q(date__lt=today)
                | Q(status__in=[
                    Appointment.Status.COMPLETED,
                    Appointment.Status.NO_SHOW,
                ])
            ).annotate(
                has_review=Exists(Review.objects.filter(appointment=OuterRef('pk')))
            ).order_by('-date', '-start_time')

        qs = qs.select_related('customer', 'barber').prefetch_related(
            'barber__shop_memberships__shop',
            'appointment_services',
        )
        return Response(AppointmentListSerializer(qs, many=True).data)


class BarberAppointmentListView(APIView):
    permission_classes = [IsBarber]

    def get(self, request):
        now = timezone.localtime()
        today = now.date()

        # Auto-complete past appointments, but only when there is at least
        # one CONFIRMED past row. Previously this fired two bulk UPDATEs on
        # every page load (including ones that affected zero rows) which
        # showed up in query logs for a mostly-clean dashboard.
        unresolved = Appointment.objects.filter(
            barber=request.user,
            status=Appointment.Status.CONFIRMED,
        ).filter(
            Q(date__lt=today) | Q(date=today, end_time__lte=now.time())
        )
        if unresolved.exists():
            unresolved.update(status=Appointment.Status.COMPLETED)

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

        appointments = list(
            Appointment.objects.filter(
                barber=request.user,
                date=target_date,
            )
            .select_related('customer', 'barber')
            .prefetch_related('barber__shop_memberships__shop', 'appointment_services')
            .order_by('start_time')
        )

        # Pre-aggregate customer-level outcome history in a single GROUP BY.
        # Without this, per-appointment risk scoring would fire one COUNT
        # query per row. With it, the whole day view stays at O(1) queries
        # for risk regardless of how many appointments are on the page.
        customer_ids = {
            a.customer_id for a in appointments
            if a.status == Appointment.Status.CONFIRMED
        }
        stats_map: dict[int, CustomerStats] = {}
        if customer_ids:
            terminal_statuses = [
                Appointment.Status.COMPLETED,
                Appointment.Status.CANCELLED,
                Appointment.Status.NO_SHOW,
            ]
            history = (
                Appointment.objects.filter(
                    customer_id__in=customer_ids,
                    status__in=terminal_statuses,
                )
                .values('customer_id')
                .annotate(
                    completed=Count('id', filter=Q(status=Appointment.Status.COMPLETED)),
                    cancelled=Count('id', filter=Q(status=Appointment.Status.CANCELLED)),
                    no_show=Count('id', filter=Q(status=Appointment.Status.NO_SHOW)),
                )
            )
            stats_map = {
                row['customer_id']: CustomerStats(
                    completed=row['completed'],
                    cancelled=row['cancelled'],
                    no_show=row['no_show'],
                )
                for row in history
            }

        serializer = AppointmentListSerializer(
            appointments,
            many=True,
            context={
                'include_risk': True,
                'customer_stats_map': stats_map,
            },
        )
        return Response(serializer.data)


class AppointmentDetailView(APIView):
    """Single-appointment lookup. Used by pages like the review form that
    need details for one booking and would otherwise have to fetch the full
    past-appointments list and filter client-side."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            appointment = (
                Appointment.objects.select_related('customer', 'barber')
                .prefetch_related('barber__shop_memberships__shop', 'appointment_services')
                .get(pk=pk)
            )
        except Appointment.DoesNotExist:
            return Response(
                {'detail': 'Appointment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user != appointment.customer and request.user != appointment.barber:
            return Response(
                {'detail': 'You do not have permission to view this appointment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(AppointmentListSerializer(appointment).data)


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


class AppointmentRescheduleView(APIView):
    """Reschedule an existing appointment in place, preserving payment."""

    permission_classes = [IsCustomer]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.select_related('barber').get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user != appointment.customer:
            return Response(
                {'detail': 'You can only reschedule your own appointments.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {'detail': 'Only confirmed appointments can be rescheduled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_date = serializer.validated_data['date']
        new_start = serializer.validated_data['start_time']
        service_ids = serializer.validated_data['service_ids']

        services = list(Service.objects.filter(pk__in=service_ids, barber=appointment.barber))
        if len(services) != len(service_ids):
            return Response(
                {'detail': 'One or more services not found for this barber.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_duration = sum(s.duration_minutes for s in services)
        total_price = sum(s.price for s in services)
        new_end = (
            datetime.datetime.combine(new_date, new_start)
            + datetime.timedelta(minutes=total_duration)
        ).time()

        with transaction.atomic():
            existing = list(
                Appointment.objects.select_for_update()
                .filter(
                    barber=appointment.barber,
                    date=new_date,
                    status=Appointment.Status.CONFIRMED,
                )
                .exclude(pk=appointment.pk)
            )
            for appt in existing:
                if _overlaps(new_start, new_end, appt.start_time, appt.end_time):
                    return Response(
                        {'detail': 'This time slot is already booked.'},
                        status=status.HTTP_409_CONFLICT,
                    )

            appointment.date = new_date
            appointment.start_time = new_start
            appointment.end_time = new_end
            appointment.total_duration = total_duration
            appointment.total_price = total_price
            appointment.save()

            AppointmentService.objects.filter(appointment=appointment).delete()
            for svc in services:
                AppointmentService.objects.create(
                    appointment=appointment,
                    service=svc,
                    service_name=svc.name,
                    service_price=svc.price,
                    service_duration=svc.duration_minutes,
                )

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


class PaymentConfigView(APIView):
    """
    Public endpoint that tells the frontend whether online payment is wired up.
    The frontend uses this to hide the "Pay Online" option entirely when
    STRIPE_SECRET_KEY isn't set, so users don't get a 503 mid-booking.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'stripe_enabled': bool(django_settings.STRIPE_SECRET_KEY),
        })


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsCustomer]

    UZS_TO_USD_RATE = 12800

    def post(self, request):
        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response(
                {'detail': 'appointment_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            appointment = Appointment.objects.select_related('barber').get(pk=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Ownership: the authenticated customer must own the appointment.
        # Without this check any logged-in customer could open a checkout for
        # a stranger's booking using just the ID.
        if appointment.customer_id != request.user.id:
            return Response({'detail': 'Not your appointment.'}, status=status.HTTP_403_FORBIDDEN)

        if appointment.payment_method != Appointment.PaymentMethod.ONLINE:
            return Response(
                {'detail': 'This appointment is not paid online.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if appointment.payment_status == Appointment.PaymentStatus.PAID:
            return Response(
                {'detail': 'This appointment is already paid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = django_settings.STRIPE_SECRET_KEY
        if not stripe.api_key:
            return Response(
                {'detail': 'Stripe not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Amount is derived from the appointment — never trust the client.
        amount_uzs = appointment.total_price
        amount_usd_cents = max(50, round(amount_uzs / self.UZS_TO_USD_RATE * 100))

        frontend_url = getattr(django_settings, 'FRONTEND_URL', 'http://localhost:5173')
        description = f'Appointment with {appointment.barber.get_full_name() or "barber"} on {appointment.date}'

        metadata = {
            'user_id': str(request.user.id),
            'appointment_id': str(appointment.id),
            'amount_uzs': str(amount_uzs),
        }

        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': description},
                        'unit_amount': amount_usd_cents,
                    },
                    'quantity': 1,
                }],
                metadata=metadata,
                success_url=(
                    f'{frontend_url}/customer/appointments?payment=success'
                    '&session_id={CHECKOUT_SESSION_ID}'
                ),
                cancel_url=f'{frontend_url}/customer/appointments?payment=cancelled',
            )
            return Response({'url': session.url, 'session_id': session.id})
        except stripe.error.StripeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FinalizeCheckoutSessionView(APIView):
    """
    Client-side fallback for flipping an appointment to PAID after the customer
    returns from Stripe. The success redirect URL now includes
    `?session_id={CHECKOUT_SESSION_ID}`; the customer appointments page POSTs
    it here. We verify the session is actually paid before marking the
    appointment.

    The webhook (`StripeWebhookView`) is the primary path in production, but
    that requires Stripe hitting a publicly reachable URL. This endpoint
    ensures the demo stays correct without webhook infra.
    """

    permission_classes = [IsCustomer]

    def post(self, request):
        stripe.api_key = django_settings.STRIPE_SECRET_KEY
        if not stripe.api_key:
            return Response(
                {'detail': 'Stripe not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'detail': 'session_id is required.'}, status=400)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            return Response({'detail': str(e)}, status=400)

        if session.payment_status != 'paid':
            return Response(
                {'detail': 'Payment is not complete.', 'status': session.payment_status},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        # session.metadata is a StripeObject. Don't .get() it (raises
        # AttributeError) and don't dict() it (raises KeyError on some SDK
        # versions whose __iter__ yields indices). getattr with a default
        # works across versions for known keys.
        md = session.metadata
        appointment_id_raw = getattr(md, 'appointment_id', None) if md else None
        meta_user_id_raw = getattr(md, 'user_id', None) if md else None
        try:
            appointment_id = int(appointment_id_raw or 0)
            meta_user_id = int(meta_user_id_raw or 0)
        except (ValueError, TypeError):
            appointment_id = 0
            meta_user_id = 0
        if not appointment_id or not meta_user_id:
            return Response({'detail': 'Session is not linked to an appointment.'}, status=400)

        # Defence in depth: the session's metadata.user_id must match both
        # the caller and the appointment's customer. Blocks the case where
        # user A shares their own session_id with user B.
        if meta_user_id != request.user.id:
            return Response({'detail': 'Not your checkout session.'}, status=403)

        try:
            appointment = Appointment.objects.get(pk=appointment_id)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found.'}, status=404)

        if appointment.customer_id != request.user.id:
            return Response({'detail': 'Not your appointment.'}, status=403)

        if appointment.payment_status != Appointment.PaymentStatus.PAID:
            appointment.payment_status = Appointment.PaymentStatus.PAID
            appointment.save(update_fields=['payment_status'])

        return Response(AppointmentSerializer(appointment).data)


class StripeWebhookView(APIView):
    """Receives `checkout.session.completed` events from Stripe.

    Security posture:
    - In non-DEBUG, STRIPE_WEBHOOK_SECRET is mandatory; unsigned requests
      are rejected. A missing secret in DEBUG falls back to raw-body parsing
      (dev only) so demos work without a tunneling tool.
    - Every update is cross-checked against metadata: the session's
      `user_id` must match the appointment's customer before we flip
      payment_status. This prevents a replay where an attacker reuses a
      genuine event body to mark someone else's booking as paid.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        stripe.api_key = django_settings.STRIPE_SECRET_KEY
        webhook_secret = getattr(django_settings, 'STRIPE_WEBHOOK_SECRET', '')
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        if not webhook_secret:
            if not django_settings.DEBUG:
                # Fail closed in production — an unauthenticated webhook can
                # mark arbitrary appointments as paid.
                return Response(
                    {'detail': 'Webhook secret not configured.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            import json
            try:
                event = json.loads(payload.decode('utf-8') or '{}')
            except ValueError:
                return Response(status=400)
        else:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            except (ValueError, stripe.error.SignatureVerificationError):
                return Response(status=400)

        event_type = event.get('type') if isinstance(event, dict) else event['type']
        if event_type != 'checkout.session.completed':
            return Response(status=200)

        data = event['data']['object'] if isinstance(event, dict) else event.data.object
        if isinstance(data, dict):
            md = data.get('metadata') or {}
            appointment_id_raw = md.get('appointment_id')
            meta_user_id_raw = md.get('user_id')
            payment_status = data.get('payment_status')
        else:
            md = data.metadata
            # Avoid .get() / dict() on StripeObject — see FinalizeCheckoutSessionView.
            appointment_id_raw = getattr(md, 'appointment_id', None) if md else None
            meta_user_id_raw = getattr(md, 'user_id', None) if md else None
            payment_status = data.payment_status
        try:
            appointment_id = int(appointment_id_raw or 0)
            meta_user_id = int(meta_user_id_raw or 0)
        except (ValueError, TypeError):
            return Response(status=400)

        if not appointment_id or not meta_user_id or payment_status != 'paid':
            return Response(status=200)

        try:
            appointment = Appointment.objects.only(
                'id', 'customer_id', 'payment_status'
            ).get(pk=appointment_id)
        except Appointment.DoesNotExist:
            return Response(status=200)

        # Metadata must match the appointment. This guards against replaying
        # a captured event body against a different appointment ID.
        if appointment.customer_id != meta_user_id:
            return Response(status=400)

        if appointment.payment_status != Appointment.PaymentStatus.PAID:
            Appointment.objects.filter(pk=appointment_id).update(
                payment_status=Appointment.PaymentStatus.PAID,
            )

        return Response(status=200)
