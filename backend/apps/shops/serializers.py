"""
DRF serializers for the shops domain.
"""

from rest_framework import serializers

from .models import BarberShopMembership, Shop, ShopHours, ShopPhoto


class ShopHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopHours
        fields = ['id', 'day_of_week', 'is_open', 'opens_at', 'closes_at', 'break_start', 'break_end']


class ShopPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopPhoto
        fields = ['id', 'image', 'uploaded_at']


class ShopSerializer(serializers.ModelSerializer):
    hours = ShopHoursSerializer(many=True, read_only=True)
    photos = ShopPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ['id', 'name', 'address', 'lat', 'lng', 'description', 'hours', 'photos', 'created_at']
        read_only_fields = ['id', 'created_at']


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarberShopMembership
        fields = ['id', 'barber', 'added_at']
        read_only_fields = ['id', 'added_at']
