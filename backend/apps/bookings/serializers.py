from rest_framework import serializers

from apps.bookings.models import Appointment, AppointmentService
from apps.bookings.risk import CustomerStats, compute_risk


class BookingCreateSerializer(serializers.Serializer):
    barber_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    service_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    payment_method = serializers.ChoiceField(
        choices=Appointment.PaymentMethod.choices,
    )


class RescheduleSerializer(serializers.Serializer):
    date = serializers.DateField()
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    service_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class AppointmentServiceSerializer(serializers.ModelSerializer):
    service_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AppointmentService
        fields = ['service_id', 'service_name', 'service_price', 'service_duration']


class AppointmentSerializer(serializers.ModelSerializer):
    services = AppointmentServiceSerializer(source='appointment_services', many=True, read_only=True)
    start_time = serializers.TimeField(format='%H:%M')
    end_time = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Appointment
        fields = [
            'id', 'customer', 'barber', 'date', 'start_time', 'end_time',
            'status', 'payment_method', 'payment_status',
            'total_price', 'total_duration', 'created_at', 'services',
        ]


class AppointmentListSerializer(serializers.ModelSerializer):
    services = AppointmentServiceSerializer(source='appointment_services', many=True, read_only=True)
    start_time = serializers.TimeField(format='%H:%M')
    end_time = serializers.TimeField(format='%H:%M')
    shop_name = serializers.SerializerMethodField()
    shop_address = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    barber_name = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()
    risk = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'customer', 'barber', 'customer_name', 'barber_name',
            'date', 'start_time', 'end_time',
            'status', 'payment_method', 'payment_status',
            'total_price', 'total_duration', 'created_at', 'services',
            'shop_name', 'shop_address', 'has_review', 'risk',
        ]

    def _get_shop(self, obj):
        # Caches once per row so `get_shop_name` + `get_shop_address` don't
        # each fire their own query. The view is expected to prefetch
        # `barber__shop_memberships__shop` so reading `.all()` is a no-op.
        if not hasattr(obj, '_cached_shop'):
            memberships = list(obj.barber.shop_memberships.all())
            obj._cached_shop = memberships[0].shop if memberships else None
        return obj._cached_shop

    def get_shop_name(self, obj):
        shop = self._get_shop(obj)
        return shop.name if shop else None

    def get_shop_address(self, obj):
        shop = self._get_shop(obj)
        return shop.address if shop else None

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.username

    def get_barber_name(self, obj):
        return obj.barber.get_full_name() or obj.barber.username

    def get_has_review(self, obj) -> bool:
        return getattr(obj, 'has_review', False)

    def get_risk(self, obj):
        # Only computed when the view explicitly opts in (barber day view).
        # Customer-facing lists never expose it. Past / non-CONFIRMED rows
        # return null — their outcome is already known.
        if not self.context.get('include_risk'):
            return None
        if obj.status != Appointment.Status.CONFIRMED:
            return None
        stats_map: dict[int, CustomerStats] = self.context.get('customer_stats_map', {})
        stats = stats_map.get(obj.customer_id, CustomerStats())
        return compute_risk(
            stats=stats,
            appointment_date=obj.date,
            appointment_time=obj.start_time,
            created_at=obj.created_at,
        )
