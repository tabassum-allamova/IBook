"""
DRF serializers for the shops domain.
"""

from datetime import datetime

from rest_framework import serializers

from apps.services.models import Service

from .models import BarberShopMembership, Shop, ShopHours, ShopPhoto


class ShopHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopHours
        fields = ['id', 'day_of_week', 'is_open', 'opens_at', 'closes_at', 'break_start', 'break_end']


class ShopPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopPhoto
        fields = ['id', 'image', 'uploaded_at']


class BarberServiceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']


class BarberSummarySerializer(serializers.Serializer):
    """Lightweight barber info for shop management page cards."""
    id = serializers.IntegerField()
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    avatar = serializers.ImageField()
    top_services = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.email

    def get_top_services(self, obj) -> list:
        services = obj.services.order_by('sort_order')[:3]
        return BarberServiceSummarySerializer(services, many=True, context=self.context).data


class MembershipDetailSerializer(serializers.ModelSerializer):
    """Membership with nested barber detail for the shop management page."""
    barber = BarberSummarySerializer(read_only=True)

    class Meta:
        model = BarberShopMembership
        fields = ['id', 'barber', 'added_at']
        read_only_fields = ['id', 'added_at']


class ShopSerializer(serializers.ModelSerializer):
    hours = ShopHoursSerializer(many=True, read_only=True)
    photos = ShopPhotoSerializer(many=True, read_only=True)
    members = MembershipDetailSerializer(source='memberships', many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ['id', 'name', 'address', 'lat', 'lng', 'description', 'hours', 'photos', 'members', 'created_at']
        read_only_fields = ['id', 'created_at']


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarberShopMembership
        fields = ['id', 'barber', 'added_at']
        read_only_fields = ['id', 'added_at']


class ShopListSerializer(serializers.ModelSerializer):
    """Lightweight shop serializer for the discovery list cards.

    Includes distance_km (from haversine_distance annotation or null),
    is_open_now (based on current time vs ShopHours), min_price (across
    all barbers in this shop), and photo (first photo URL or null).
    """

    photo = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            'id', 'name', 'address', 'lat', 'lng',
            'photo', 'distance_km', 'is_open_now', 'min_price', 'avg_rating',
        ]

    def get_photo(self, obj) -> str | None:
        photo = obj.photos.first()
        if photo and self.context.get('request'):
            return self.context['request'].build_absolute_uri(photo.image.url)
        return None

    def get_distance_km(self, obj) -> float | None:
        dist = getattr(obj, 'haversine_distance', None)
        if dist is None:
            return None
        return round(float(dist), 1)

    def get_is_open_now(self, obj) -> bool:
        now = datetime.now()
        day = now.weekday()  # Monday=0 matches ShopHours DAYS
        try:
            hours = obj.hours.get(day_of_week=day, is_open=True)
            return hours.opens_at <= now.time() <= hours.closes_at
        except Exception:
            return False

    def get_min_price(self, obj) -> int | None:
        """Minimum service price across all barbers in this shop."""
        result = (
            Service.objects
            .filter(barber__shop_memberships__shop=obj)
            .order_by('price')
            .values_list('price', flat=True)
            .first()
        )
        return result

    def get_avg_rating(self, obj) -> float | None:
        """Returns average rating aggregated across all barbers in this shop."""
        from django.db.models import Avg
        from apps.reviews.models import Review
        result = Review.objects.filter(
            barber__shop_memberships__shop=obj
        ).aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None
