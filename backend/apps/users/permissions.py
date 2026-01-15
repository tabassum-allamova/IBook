"""
IBook DRF permission classes.

Provides role-based access control for API endpoints.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsCustomer(BasePermission):
    """Allow access only to authenticated users with role=CUSTOMER."""

    message = "Access restricted to customers only."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "CUSTOMER"
        )


class IsBarber(BasePermission):
    """Allow access only to authenticated users with role=BARBER."""

    message = "Access restricted to barbers only."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "BARBER"
        )


class IsShopOwner(BasePermission):
    """Allow access only to authenticated users with role=SHOP_OWNER."""

    message = "Access restricted to shop owners only."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "SHOP_OWNER"
        )


class IsOwnerOrBarber(BasePermission):
    """Allow access to authenticated users with role=BARBER or SHOP_OWNER."""

    message = "Access restricted to barbers and shop owners only."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("BARBER", "SHOP_OWNER")
        )
