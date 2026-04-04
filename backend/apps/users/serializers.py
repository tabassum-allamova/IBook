import re

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import CustomUser


def _validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[a-zA-Z]", password):
        raise serializers.ValidationError("Password must contain at least one letter.")
    if not re.search(r"[0-9]", password):
        raise serializers.ValidationError("Password must contain at least one number.")
    return password


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


class CustomerRegisterSerializer(serializers.Serializer):
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


class BarberProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    bio = serializers.CharField()
    years_of_experience = serializers.IntegerField(allow_null=True)
    services = serializers.SerializerMethodField()
    weekly_schedule = serializers.SerializerMethodField()
    shop_name = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    def get_full_name(self, obj: CustomUser) -> str:
        return obj.get_full_name() or obj.email

    def get_avatar(self, obj: CustomUser) -> str | None:
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url

    def get_services(self, obj: CustomUser) -> list:
        from apps.services.models import Service
        services = Service.objects.filter(barber=obj).order_by('sort_order')
        return [
            {
                'id': svc.id,
                'name': svc.name,
                'price': svc.price,
                'duration_minutes': svc.duration_minutes,
            }
            for svc in services
        ]

    def get_weekly_schedule(self, obj: CustomUser) -> list:
        from apps.services.models import WeeklySchedule
        schedule = WeeklySchedule.objects.filter(barber=obj).order_by('day_of_week')
        return [
            {
                'day_of_week': entry.day_of_week,
                'is_working': entry.is_working,
                'start_time': str(entry.start_time) if entry.start_time else None,
                'end_time': str(entry.end_time) if entry.end_time else None,
            }
            for entry in schedule
        ]

    def get_shop_name(self, obj: CustomUser) -> str | None:
        membership = obj.shop_memberships.select_related('shop').first()
        return membership.shop.name if membership else None

    def get_avg_rating(self, obj: CustomUser) -> float | None:
        from django.db.models import Avg
        from apps.reviews.models import Review
        result = Review.objects.filter(barber=obj).aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None
