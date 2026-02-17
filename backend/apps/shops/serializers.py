"""
DRF serializers for the shops domain.
"""

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
