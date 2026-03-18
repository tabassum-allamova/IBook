"""
IBook auth API views.

Provides:
  - CustomerRegisterView
  - ProfessionalRegisterView
  - VerifyEmailView
  - LoginView
  - LogoutView
  - CookieTokenRefreshView
  - ProfileView

All views live under the /api/auth/ prefix (configured in config/urls.py).
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import CustomUser
from apps.users.serializers import (
    BarberProfileSerializer,
    CustomerRegisterSerializer,
    CustomTokenObtainPairSerializer,
    ProfessionalRegisterSerializer,
    UserProfileSerializer,
)

_signer = TimestampSigner()
_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds


def _send_verification_email(user: CustomUser) -> None:
    """Sign the user PK and email a verification link. Runs in a thread to avoid blocking."""
    import threading

    token = _signer.sign(user.pk)
    # Link goes directly to Django API which verifies and redirects to login
    verify_url = f"http://localhost:8000/api/auth/verify-email/?token={token}"

    def _send():
        send_mail(
            subject="Verify your IBook account",
            message=f"Click to verify your email: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    threading.Thread(target=_send, daemon=True).start()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach an httpOnly refresh cookie to *response*."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=_REFRESH_MAX_AGE,
        httponly=True,
        secure=False,  # Set to True in production (HTTPS)
        samesite="Lax",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class CustomerRegisterView(APIView):
    """POST /api/auth/register/customer/ — create a customer account."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _send_verification_email(user)
        return Response(
            {"email": user.email, "role": user.role},
            status=status.HTTP_201_CREATED,
        )


class ProfessionalRegisterView(APIView):
    """POST /api/auth/register/professional/ — create a barber or shop-owner account."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ProfessionalRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _send_verification_email(user)
        return Response(
            {"email": user.email, "role": user.role},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


class VerifyEmailView(APIView):
    """GET /api/auth/verify-email/?token=... — activate account after email link click."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        token = request.query_params.get("token", "")
        if not token:
            return Response(
                {"detail": "Verification token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # 24-hour expiry
            user_pk = _signer.unsign(token, max_age=86400)
        except SignatureExpired:
            return Response(
                {"detail": "Verification link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except BadSignature:
            return Response(
                {"detail": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = CustomUser.objects.get(pk=user_pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.is_active = True
        user.is_email_verified = True
        user.save(update_fields=["is_active", "is_email_verified"])
        # Redirect to frontend login page with success message
        from django.shortcuts import redirect
        return redirect(f"{settings.FRONTEND_URL}/login?verified=true")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginView(APIView):
    """POST /api/auth/login/ — obtain JWT pair; refresh token goes into httpOnly cookie."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CustomTokenObtainPairSerializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            raise

        tokens = serializer.validated_data
        user: CustomUser = serializer.user  # type: ignore[assignment]

        response = Response(
            {
                "access": tokens["access"],
                "user": {
                    "id": user.pk,
                    "role": user.role,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                },
            },
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, tokens["refresh"])
        return response


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the refresh token and clear the cookie."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get(_REFRESH_COOKIE)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Already blacklisted or invalid — still clear the cookie

        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        response.delete_cookie(_REFRESH_COOKIE)
        return response


# ---------------------------------------------------------------------------
# Token refresh (reads from cookie)
# ---------------------------------------------------------------------------


class CookieTokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/

    Reads the refresh token from the httpOnly cookie instead of the request body.
    Returns a new access token in the response body and sets a new refresh cookie.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer

        refresh_token = request.COOKIES.get(_REFRESH_COOKIE)
        if not refresh_token:
            return Response(
                {"detail": "Refresh token cookie not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(
            {"access": serializer.validated_data["access"]},
            status=status.HTTP_200_OK,
        )
        # Set new refresh cookie if rotation produced a new refresh token
        new_refresh = serializer.validated_data.get("refresh")
        if new_refresh:
            _set_refresh_cookie(response, new_refresh)

        return response


# ---------------------------------------------------------------------------
# Stub views for permission testing (Phase 3 will replace with real implementations)
# ---------------------------------------------------------------------------


class BarberDashboardStubView(APIView):
    """GET /api/barbers/dashboard/ — stub endpoint to test IsBarber permission.
    Phase 3 will replace this with the real barber dashboard view.
    """

    from apps.users.permissions import IsBarber  # forward reference resolved at class time

    permission_classes = [IsBarber]

    def get(self, request: Request) -> Response:
        return Response({"detail": "Barber dashboard (stub)"}, status=status.HTTP_200_OK)


class ShopOwnerDashboardStubView(APIView):
    """GET /api/shops/dashboard/ — stub endpoint to test IsShopOwner permission.
    Phase 3 will replace this with the real shop owner dashboard view.
    """

    from apps.users.permissions import IsShopOwner  # forward reference resolved at class time

    permission_classes = [IsShopOwner]

    def get(self, request: Request) -> Response:
        return Response({"detail": "Shop owner dashboard (stub)"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class ProfileView(RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/profile/ — read or update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = UserProfileSerializer

    def get_object(self) -> CustomUser:
        return self.request.user  # type: ignore[return-value]

    def update(self, request: Request, *args, **kwargs) -> Response:
        kwargs["partial"] = True  # Always partial — PATCH semantics
        return super().update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Barber profile (Phase 4 - Discovery)
# ---------------------------------------------------------------------------


class BarberProfileView(APIView):
    """
    GET /api/barbers/<pk>/ — retrieve full barber profile.

    Accessible to any authenticated user (customer, barber, or shop owner).
    Returns 404 if the user does not exist or is not a barber.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        barber = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.BARBER)
        serializer = BarberProfileSerializer(barber, context={'request': request})
        return Response(serializer.data)
