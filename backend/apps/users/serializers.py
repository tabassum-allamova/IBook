"""
IBook authentication serializers.

Provides:
  - CustomerRegisterSerializer
  - ProfessionalRegisterSerializer
  - CustomTokenObtainPairSerializer
  - UserProfileSerializer
"""

import re

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import CustomUser


def _validate_password_strength(password: str) -> str:
    """Shared password validator: min 8 chars, at least one letter and one number."""
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[a-zA-Z]", password):
        raise serializers.ValidationError("Password must contain at least one letter.")
    if not re.search(r"[0-9]", password):
        raise serializers.ValidationError("Password must contain at least one number.")
    return password


def _split_full_name(full_name: str) -> tuple[str, str]:
    """Split 'full_name' into (first_name, last_name). Handle single-word names."""
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


class CustomerRegisterSerializer(serializers.Serializer):
    """Serializer for customer registration."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        existing = CustomUser.objects.filter(email__iexact=value).first()
        if existing:
            if not existing.is_email_verified:
                existing.delete()
            else:
                raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def validate_password(self, value: str) -> str:
        return _validate_password_strength(value)

    def create(self, validated_data: dict) -> CustomUser:
        first_name, last_name = _split_full_name(validated_data["full_name"])
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["email"],
            password=validated_data["password"],
            role=CustomUser.Role.CUSTOMER,
            first_name=first_name,
            last_name=last_name,
            phone_number=validated_data.get("phone_number", ""),
            is_active=False,
            is_email_verified=False,
        )
        return user


class ProfessionalRegisterSerializer(serializers.Serializer):
    """Serializer for barber / shop-owner registration."""

    ALLOWED_ROLES = [CustomUser.Role.BARBER, CustomUser.Role.SHOP_OWNER]

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=ALLOWED_ROLES)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        existing = CustomUser.objects.filter(email__iexact=value).first()
        if existing:
            if not existing.is_email_verified:
                existing.delete()
            else:
                raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def validate_password(self, value: str) -> str:
        return _validate_password_strength(value)

    def create(self, validated_data: dict) -> CustomUser:
        first_name, last_name = _split_full_name(validated_data["full_name"])
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            first_name=first_name,
            last_name=last_name,
            phone_number=validated_data.get("phone_number", ""),
            is_active=False,
            is_email_verified=False,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT serializer that embeds role, email, and full_name into the access token."""

    @classmethod
    def get_token(cls, user: CustomUser):  # type: ignore[override]
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        user: CustomUser = self.user  # type: ignore[assignment]
        if not user.is_email_verified:
            raise AuthenticationFailed(
                "Email not verified. Please verify your email before logging in."
            )
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating a user's profile.

    Read: all profile fields.
    Write (PATCH): first_name, last_name, phone_number, avatar, bio, years_of_experience.
    Role is always read-only.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "role",
            "full_name",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "bio",
            "years_of_experience",
            "is_email_verified",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_email_verified", "date_joined"]

    def get_full_name(self, obj: CustomUser) -> str:
        return obj.get_full_name()
