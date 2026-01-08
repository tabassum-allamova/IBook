from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser — extends the built-in UserAdmin."""

    list_display = ("email", "username", "role", "is_email_verified", "is_active", "date_joined")
    list_filter = ("role", "is_email_verified", "is_active", "is_staff")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": (
                    "role",
                    "is_email_verified",
                    "phone_number",
                    "avatar",
                    "bio",
                    "years_of_experience",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Profile",
            {
                "fields": ("role",),
            },
        ),
    )
