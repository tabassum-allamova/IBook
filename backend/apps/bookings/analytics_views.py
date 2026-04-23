from datetime import date, timedelta

from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, AppointmentService
from apps.users.permissions import IsBarber, IsShopOwner


_PERIOD_DAYS = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
}


def _period_days(period: str) -> int | None:
    return _PERIOD_DAYS.get(period)


def _since_date(period: str):
    days = _period_days(period)
    if days is None:
        return None
    return date.today() - timedelta(days=days)


def _build_trend(qs):
    """Group appointments by date for trend chart."""
    rows = (
        qs
        .values('date')
        .annotate(count=Count('id'), revenue=Sum('total_price'))
        .order_by('date')
    )
    return [
        {
            'day': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
            'count': row['count'],
            'revenue': row['revenue'] or 0,
        }
        for row in rows
    ]


def _fill_daily_series(trend_rows, start: date, end: date):
    """Return one entry per day in [start, end], zero-filled for missing days."""
    by_day = {row['day']: row for row in trend_rows}
    out = []
    day = start
    while day <= end:
        key = day.isoformat()
        match = by_day.get(key)
        out.append({
            'day': key,
            'count': match['count'] if match else 0,
            'revenue': match['revenue'] if match else 0,
        })
        day += timedelta(days=1)
    return out


def _moving_average_forecast(values, horizon: int = 7, window: int = 14):
    """Flat-line projection using the recent mean.

    A moving-average forecast is the standard simple baseline and is robust to
    occasional zero days (weekends, off-days) that would otherwise drag a
    linear-regression slope toward zero. We use an EWMA-style weighting so the
    last week counts more than the week before it.
    """
    if not values:
        return [0.0] * horizon
    recent = values[-window:] if len(values) >= window else values
    n = len(recent)
    # Exponential weights: newer values count more.
    weights = [0.85 ** (n - 1 - i) for i in range(n)]
    wsum = sum(weights)
    avg = sum(v * w for v, w in zip(recent, weights)) / wsum if wsum > 0 else 0
    return [max(0.0, avg)] * horizon


def _forecast_series(daily_series, horizon: int = 7):
    counts = [row['count'] for row in daily_series]
    revenues = [float(row['revenue']) for row in daily_series]
    pred_counts = _moving_average_forecast(counts, horizon)
    pred_revenues = _moving_average_forecast(revenues, horizon)
    last_day = date.fromisoformat(daily_series[-1]['day']) if daily_series else date.today()
    out = []
    for i in range(horizon):
        day = last_day + timedelta(days=i + 1)
        out.append({
            'day': day.isoformat(),
            'count': round(pred_counts[i], 2),
            'revenue': round(pred_revenues[i]),
        })
    return out


def _top_services(qs, limit: int = 6):
    rows = (
        AppointmentService.objects.filter(appointment__in=qs)
        .values('service_name')
        .annotate(count=Count('id'), revenue=Sum('service_price'))
        .order_by('-count')[:limit]
    )
    return [
        {
            'name': r['service_name'],
            'count': r['count'],
            'revenue': r['revenue'] or 0,
        }
        for r in rows
    ]


def _day_of_week_breakdown(qs):
    """Counts per weekday. Mon=0, Sun=6.

    Aggregated by the database instead of iterating rows in Python. Django's
    ExtractWeekDay returns 1=Sunday…7=Saturday (portable across backends),
    which we remap to the Mon=0…Sun=6 convention our frontend uses.
    """
    buckets = [0] * 7
    revenues = [0] * 7
    rows = (
        qs.annotate(dow=ExtractWeekDay('date'))
        .values('dow')
        .annotate(count=Count('id'), revenue=Sum('total_price'))
    )
    for row in rows:
        # ExtractWeekDay: 1=Sun, 2=Mon, …, 7=Sat  →  Python: 6,0,1,…,5
        iso = (row['dow'] - 2) % 7
        buckets[iso] = row['count']
        revenues[iso] = float(row['revenue'] or 0)
    return [
        {'day_of_week': i, 'count': buckets[i], 'revenue': round(revenues[i])}
        for i in range(7)
    ]


def _hour_of_day_breakdown(qs):
    buckets = [0] * 24
    rows = (
        qs.annotate(hr=ExtractHour('start_time'))
        .values('hr')
        .annotate(count=Count('id'))
    )
    for row in rows:
        h = row['hr']
        if h is not None and 0 <= h < 24:
            buckets[h] = row['count']
    return [{'hour': i, 'count': buckets[i]} for i in range(24)]


class BarberAnalyticsView(APIView):
    permission_classes = [IsBarber]

    def get(self, request):
        from apps.reviews.models import Review

        period = request.query_params.get('period', '30d')
        since = _since_date(period)
        period_days = _period_days(period)
        today = date.today()

        # Real business activity: completed + confirmed past/today appointments.
        base = Appointment.objects.filter(
            barber=request.user,
            status__in=[Appointment.Status.COMPLETED, Appointment.Status.CONFIRMED],
            date__lte=today,
        )
        qs = base.filter(date__gte=since) if since is not None else base

        # ---- Totals ----
        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
            avg_ticket=Avg('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0
        avg_ticket = round(totals['avg_ticket'] or 0)

        # ---- Previous-period comparison ----
        previous = {'total_bookings': 0, 'total_revenue': 0}
        if period_days is not None:
            prev_start = today - timedelta(days=period_days * 2)
            prev_end = today - timedelta(days=period_days + 1)
            prev_qs = base.filter(date__gte=prev_start, date__lte=prev_end)
            prev_totals = prev_qs.aggregate(
                total_bookings=Count('id'),
                total_revenue=Sum('total_price'),
            )
            previous = {
                'total_bookings': prev_totals['total_bookings'] or 0,
                'total_revenue': prev_totals['total_revenue'] or 0,
            }

        # ---- Trend + 7-day forecast ----
        trend = _build_trend(qs)
        series_end = today - timedelta(days=1)
        if since is not None:
            series = _fill_daily_series(trend, since, series_end)
        else:
            if trend:
                start = date.fromisoformat(trend[0]['day'])
                end = min(series_end, date.fromisoformat(trend[-1]['day']))
                series = _fill_daily_series(trend, start, end)
            else:
                series = []
        forecast = _forecast_series(series, horizon=7) if series else []

        # ---- Top services (count + revenue) ----
        top_services = list(
            AppointmentService.objects.filter(appointment__in=qs)
            .values('service_name')
            .annotate(count=Count('id'), revenue=Sum('service_price'))
            .order_by('-count')[:6]
        )
        top_services = [
            {'name': r['service_name'], 'count': r['count'], 'revenue': r['revenue'] or 0}
            for r in top_services
        ]

        # ---- Outcome breakdown (completed / cancelled / no-show) ----
        # Use the wider window including cancellations so the barber can see
        # how often bookings fall through.
        outcome_window = Appointment.objects.filter(
            barber=request.user,
            date__lte=today,
        )
        if since is not None:
            outcome_window = outcome_window.filter(date__gte=since)
        outcome_counts = {
            row['status']: row['count']
            for row in outcome_window.values('status').annotate(count=Count('id'))
        }
        status_breakdown = {
            'completed': outcome_counts.get(Appointment.Status.COMPLETED, 0),
            'confirmed': outcome_counts.get(Appointment.Status.CONFIRMED, 0),
            'cancelled': outcome_counts.get(Appointment.Status.CANCELLED, 0),
            'no_show': outcome_counts.get(Appointment.Status.NO_SHOW, 0),
        }
        total_with_cancelled = sum(status_breakdown.values())
        completion_rate = (
            round(status_breakdown['completed'] * 100 / total_with_cancelled, 1)
            if total_with_cancelled > 0
            else None
        )

        # ---- Repeat-customer rate ----
        # Share of bookings from customers who have booked this barber more
        # than once (within the selected window). Measures loyalty.
        customer_counts = list(
            qs.values('customer_id').annotate(n=Count('id'))
        )
        unique_customers = len(customer_counts)
        repeat_customers = sum(1 for c in customer_counts if c['n'] > 1)
        repeat_bookings = sum(c['n'] for c in customer_counts if c['n'] > 1)
        repeat_rate = (
            round(repeat_bookings * 100 / total_bookings, 1)
            if total_bookings > 0
            else None
        )

        # ---- Ratings summary + distribution + recent reviews ----
        reviews_qs = Review.objects.filter(barber=request.user)
        agg = reviews_qs.aggregate(avg=Avg('rating'), count=Count('id'))
        avg_rating = round(agg['avg'], 1) if agg['avg'] is not None else None
        review_count = agg['count'] or 0

        distribution = {str(i): 0 for i in range(1, 6)}
        for row in reviews_qs.values('rating').annotate(count=Count('id')):
            key = str(row['rating'])
            if key in distribution:
                distribution[key] = row['count']

        recent_reviews = [
            {
                'reviewer': (
                    r.reviewer.get_full_name() or r.reviewer.email.split('@')[0]
                ),
                'rating': r.rating,
                'text': r.text or '',
                'date': r.created_at.date().isoformat(),
            }
            for r in reviews_qs.select_related('reviewer').order_by('-created_at')[:5]
        ]

        return Response({
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'avg_ticket': avg_ticket,
            'previous': previous,
            'series': series,
            'forecast': forecast,
            'top_services': top_services,
            'day_of_week': _day_of_week_breakdown(qs),
            'hour_of_day': _hour_of_day_breakdown(qs),
            'status_breakdown': status_breakdown,
            'completion_rate': completion_rate,
            'unique_customers': unique_customers,
            'repeat_customers': repeat_customers,
            'repeat_rate': repeat_rate,
            'ratings': {
                'avg': avg_rating,
                'count': review_count,
                'distribution': distribution,
                'recent': recent_reviews,
            },
        })


class OwnerAnalyticsView(APIView):
    permission_classes = [IsShopOwner]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        since = _since_date(period)
        period_days = _period_days(period)

        # Include COMPLETED + CONFIRMED (past/today). A same-day confirmed booking
        # is real business activity even if the barber hasn't flipped the status
        # to COMPLETED yet, and excluding it made recent days look empty.
        today = date.today()
        base = Appointment.objects.filter(
            barber__shop_memberships__shop__owner=request.user,
            status__in=[Appointment.Status.COMPLETED, Appointment.Status.CONFIRMED],
            date__lte=today,
        )
        qs = base.filter(date__gte=since) if since is not None else base

        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
            avg_ticket=Avg('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0
        avg_ticket = round(totals['avg_ticket'] or 0)

        # Previous-period comparison
        previous = {'total_bookings': 0, 'total_revenue': 0}
        if period_days is not None:
            prev_start = date.today() - timedelta(days=period_days * 2)
            prev_end = date.today() - timedelta(days=period_days + 1)
            prev_qs = base.filter(date__gte=prev_start, date__lte=prev_end)
            prev_totals = prev_qs.aggregate(
                total_bookings=Count('id'),
                total_revenue=Sum('total_price'),
            )
            previous = {
                'total_bookings': prev_totals['total_bookings'] or 0,
                'total_revenue': prev_totals['total_revenue'] or 0,
            }

        trend = _build_trend(qs)
        # Trim series to yesterday — today is still being booked so counting it
        # as a zero day would artificially drag the average down.
        series_end = today - timedelta(days=1)
        if since is not None:
            series = _fill_daily_series(trend, since, series_end)
        else:
            # "All time" — use first/last observed dates if available.
            if trend:
                start = date.fromisoformat(trend[0]['day'])
                end = min(series_end, date.fromisoformat(trend[-1]['day']))
                series = _fill_daily_series(trend, start, end)
            else:
                series = []

        forecast = _forecast_series(series, horizon=7) if series else []

        barber_rows = (
            qs
            .values('barber__id', 'barber__first_name', 'barber__last_name')
            .annotate(bookings=Count('id'), revenue=Sum('total_price'))
            .order_by('-bookings')
        )
        barbers = [
            {
                'id': row['barber__id'],
                'name': f"{row['barber__first_name']} {row['barber__last_name']}".strip(),
                'bookings': row['bookings'],
                'revenue': row['revenue'] or 0,
            }
            for row in barber_rows
        ]

        return Response({
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'avg_ticket': avg_ticket,
            'previous': previous,
            'trend': trend,
            'series': series,
            'forecast': forecast,
            'top_services': _top_services(qs),
            'day_of_week': _day_of_week_breakdown(qs),
            'hour_of_day': _hour_of_day_breakdown(qs),
            'barbers': barbers,
        })
