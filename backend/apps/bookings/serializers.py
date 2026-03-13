"""
Booking serializers.

Provides serializers for booking creation, appointment detail/listing,
and supporting nested representations.
"""

from rest_framework import serializers

from apps.bookings.models import Appointment, AppointmentService


class BookingCreateSerializer(serializers.Serializer):
    """Validates input for POST /api/bookings/."""

    barber_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    service_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    payment_method = serializers.ChoiceField(
        choices=Appointment.PaymentMethod.choices,
    )
    card_number = serializers.CharField(required=False, allow_blank=True, default='')


class AppointmentServiceSerializer(serializers.ModelSerializer):
    """Read-only nested representation of a service snapshot within an appointment."""

    service_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AppointmentService
        fields = ['service_id', 'service_name', 'service_price', 'service_duration']


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for booking creation response and detail views.

    Returns barber as PK integer for simple consumption by frontend.
    """

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
    """
    Serializer for listing views -- includes shop info via barber membership.
    """

    services = AppointmentServiceSerializer(source='appointment_services', many=True, read_only=True)
    start_time = serializers.TimeField(format='%H:%M')
    end_time = serializers.TimeField(format='%H:%M')
    shop_name = serializers.SerializerMethodField()
    shop_address = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    barber_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'customer', 'barber', 'customer_name', 'barber_name',
            'date', 'start_time', 'end_time',
            'status', 'payment_method', 'payment_status',
            'total_price', 'total_duration', 'created_at', 'services',
            'shop_name', 'shop_address',
        ]

    def _get_shop(self, obj):
        """Get the shop from barber's membership (cached)."""
        membership = obj.barber.shop_memberships.select_related('shop').first()
        return membership.shop if membership else None

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
