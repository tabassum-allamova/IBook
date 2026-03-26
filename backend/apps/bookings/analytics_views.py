"""
Analytics API views.

Provides aggregated booking data for barber and shop-owner dashboards.
Covers ANLT-01 (barber analytics), ANLT-02 (owner analytics), ANLT-03 (period filter).
"""

from datetime import date, timedelta

from django.db.models import Avg, Count, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, AppointmentService
from apps.users.permissions import IsBarber, IsShopOwner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PERIOD_DAYS = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
}


def _since_date(period: str):
    """
    Return the cutoff date for the given period string, or None for 'all'.

    Args:
        period: One of '7d', '30d', '90d', or 'all'.

    Returns:
        A date object (date.today() - timedelta(days=N)) or None when period='all'.
    """
    days = _PERIOD_DAYS.get(period)
    if days is None:
        return None
    return date.today() - timedelta(days=days)


def _build_trend(qs):
    """
    Group appointments by date and return a trend list.

    Each entry: {'day': 'YYYY-MM-DD', 'count': N, 'revenue': N}

    Appointment.date is already a DateField so we group directly on 'date'
    without TruncDate (which fails on DateField in SQLite).
    The day value is converted to an ISO string to ensure JSON-safe output.
    """
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


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class BarberAnalyticsView(APIView):
    """
    GET /api/bookings/analytics/barber/

    Returns aggregated analytics for the authenticated barber.

    Query params:
        period (str): '7d' | '30d' | '90d' | 'all'  (default '30d')

    Response shape:
        {
            total_bookings: int,
            total_revenue: int,
            trend: [{day: str, count: int, revenue: int}, ...],
            top_services: [{service_name: str, count: int}, ...],
            ratings_summary: {avg: float|null, count: int},
        }
    """

    permission_classes = [IsBarber]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        since = _since_date(period)

        # Base queryset: only COMPLETED appointments for this barber
        qs = Appointment.objects.filter(
            barber=request.user,
            status=Appointment.Status.COMPLETED,
        )
        if since is not None:
            qs = qs.filter(date__gte=since)

        # Aggregate totals
        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0

        # Trend: date-bucketed bookings and revenue
        trend = _build_trend(qs)

        # Top services (up to 5), sorted by usage count descending
        top_services = list(
            AppointmentService.objects.filter(appointment__in=qs)
            .values('service_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Ratings summary — all-time, not period-filtered
        ratings_summary = {'avg': None, 'count': 0}
        try:
            from apps.reviews.models import Review  # noqa: PLC0415
            agg = Review.objects.filter(barber=request.user).aggregate(
                avg=Avg('rating'),
                count=Count('id'),
            )
            avg = agg['avg']
            if avg is not None:
                avg = round(avg, 1)
            ratings_summary = {'avg': avg, 'count': agg['count'] or 0}
        except ImportError:
            # reviews app not installed yet — return empty summary
            pass

        return Response({
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'trend': trend,
            'top_services': top_services,
            'ratings_summary': ratings_summary,
        })


class OwnerAnalyticsView(APIView):
    """
    GET /api/bookings/analytics/owner/

    Returns shop-wide aggregated analytics for the authenticated shop owner.

    Query params:
        period (str): '7d' | '30d' | '90d' | 'all'  (default '30d')

    Response shape:
        {
            total_bookings: int,
            total_revenue: int,
            trend: [{day: str, count: int, revenue: int}, ...],
            barbers: [{id: int, name: str, bookings: int, revenue: int}, ...],
        }
    """

    permission_classes = [IsShopOwner]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        since = _since_date(period)

        # Base queryset: COMPLETED appointments for all barbers in this owner's shop
        qs = Appointment.objects.filter(
            barber__shop_memberships__shop__owner=request.user,
            status=Appointment.Status.COMPLETED,
        )
        if since is not None:
            qs = qs.filter(date__gte=since)

        # Shop-wide totals
        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0

        # Trend: date-bucketed shop-wide bookings and revenue
        trend = _build_trend(qs)

        # Per-barber breakdown
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
            'trend': trend,
            'barbers': barbers,
        })
