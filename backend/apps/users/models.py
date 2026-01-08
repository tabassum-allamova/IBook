from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model for IBook — extends AbstractUser with role and profile fields.
    AUTH_USER_MODEL must point here before any migration runs.
    """

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        BARBER = "BARBER", "Barber"
        SHOP_OWNER = "SHOP_OWNER", "Shop Owner"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    is_email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"
