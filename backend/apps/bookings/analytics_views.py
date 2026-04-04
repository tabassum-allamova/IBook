from datetime import date, timedelta

from django.db.models import Avg, Count, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, AppointmentService
from apps.users.permissions import IsBarber, IsShopOwner


_PERIOD_DAYS = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
}


def _since_date(period: str):
    days = _PERIOD_DAYS.get(period)
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


class BarberAnalyticsView(APIView):
    permission_classes = [IsBarber]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        since = _since_date(period)

        qs = Appointment.objects.filter(
            barber=request.user,
            status=Appointment.Status.COMPLETED,
        )
        if since is not None:
            qs = qs.filter(date__gte=since)

        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0

        trend = _build_trend(qs)

        top_services = list(
            AppointmentService.objects.filter(appointment__in=qs)
            .values('service_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

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
            pass

        return Response({
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'trend': trend,
            'top_services': top_services,
            'ratings_summary': ratings_summary,
        })


class OwnerAnalyticsView(APIView):
    permission_classes = [IsShopOwner]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        since = _since_date(period)

        qs = Appointment.objects.filter(
            barber__shop_memberships__shop__owner=request.user,
            status=Appointment.Status.COMPLETED,
        )
        if since is not None:
            qs = qs.filter(date__gte=since)

        totals = qs.aggregate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price'),
        )
        total_bookings = totals['total_bookings'] or 0
        total_revenue = totals['total_revenue'] or 0

        trend = _build_trend(qs)

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
