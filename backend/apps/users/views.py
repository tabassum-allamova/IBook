from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import CustomUser
from apps.users.serializers import (
    BarberListItemSerializer,
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
    import threading

    token = _signer.sign(user.pk)
    # Point the email at the frontend so the user lands inside the app (not on
    # the bare backend JSON response). The frontend page calls the API to
    # complete verification and then routes to /login?verified=true.
    frontend_url = getattr(settings, 'FRONTEND_URL', None) or 'http://localhost:5173'
    verify_url = f"{frontend_url.rstrip('/')}/verify-email?token={token}"

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
    # Only send the refresh cookie over HTTPS in non-DEBUG (production).
    # DEBUG keeps it flexible so developers hitting http://localhost still work.
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=_REFRESH_MAX_AGE,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )


class CustomerRegisterView(APIView):
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


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        token = request.query_params.get("token", "")
        if not token:
            return Response(
                {"detail": "Verification token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user_pk = _signer.unsign(token, max_age=86400)  # 24h expiry
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
        # The frontend /verify-email page consumes this response and shows
        # success / error inline before sending the user to the login screen.
        return Response({"detail": "Email verified."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    from rest_framework.throttling import AnonRateThrottle

    class _LoginRateThrottle(AnonRateThrottle):
        scope = 'login'
        rate = '10/min'

    permission_classes = [AllowAny]
    throttle_classes = [_LoginRateThrottle]

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


class LogoutView(APIView):
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


class CookieTokenRefreshView(APIView):
    from rest_framework.throttling import AnonRateThrottle

    class _RefreshRateThrottle(AnonRateThrottle):
        # Token-refresh requests from the same IP are capped to prevent
        # brute-forcing expired refresh tokens or abusing the cookie endpoint.
        scope = 'token_refresh'
        rate = '20/min'

    permission_classes = [AllowAny]
    throttle_classes = [_RefreshRateThrottle]

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
        new_refresh = serializer.validated_data.get("refresh")
        if new_refresh:
            _set_refresh_cookie(response, new_refresh)

        return response


class BarberDashboardStubView(APIView):
    from apps.users.permissions import IsBarber

    permission_classes = [IsBarber]

    def get(self, request: Request) -> Response:
        return Response({"detail": "Barber dashboard (stub)"}, status=status.HTTP_200_OK)


class ShopOwnerDashboardStubView(APIView):
    from apps.users.permissions import IsShopOwner

    permission_classes = [IsShopOwner]

    def get(self, request: Request) -> Response:
        return Response({"detail": "Shop owner dashboard (stub)"}, status=status.HTTP_200_OK)


class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    serializer_class = UserProfileSerializer

    def get_object(self) -> CustomUser:
        return self.request.user  # type: ignore[return-value]

    def update(self, request: Request, *args, **kwargs) -> Response:
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class BarberProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        # Prefetch everything BarberProfileSerializer touches in its method
        # fields (services, weekly schedule, shop membership, reviews) so the
        # endpoint runs in a constant number of queries instead of 4–5 per
        # call. Serializer methods will pick up the prefetched relations
        # transparently via Django's default relation cache.
        barber = get_object_or_404(
            CustomUser.objects.prefetch_related(
                'services',
                'weekly_schedule',
                'shop_memberships__shop',
                'reviews_received',
            ),
            pk=pk,
            role=CustomUser.Role.BARBER,
        )
        serializer = BarberProfileSerializer(barber, context={'request': request})
        return Response(serializer.data)


class BarberListView(APIView):
    """
    Public directory of barbers.

    Query params:
      - solo=true           → only barbers with no shop membership
      - name=...            → case-insensitive substring match on first/last name
      - email=...           → substring match on email (authenticated shop
                              owners only — used by the add-barber flow)
      - exclude_shop=<id>   → hide barbers already in this shop
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        from django.db.models import Avg, Min, Prefetch
        from apps.reviews.models import Review
        from apps.services.models import Service

        qs = (
            CustomUser.objects.filter(
                role=CustomUser.Role.BARBER,
                is_active=True,
                is_email_verified=True,
            )
            .annotate(
                _min_price=Min('services__price'),
                _avg_rating=Avg('reviews_received__rating'),
            )
            .prefetch_related(
                'shop_memberships__shop',
                Prefetch(
                    'services',
                    queryset=Service.objects.order_by('sort_order', 'price'),
                ),
            )
        )

        if request.query_params.get('solo') in ('1', 'true', 'True'):
            qs = qs.filter(shop_memberships__isnull=True)

        name = request.query_params.get('name')
        if name:
            # Split on whitespace so "Aziz Karimov" matches first_name="Aziz",
            # last_name="Karimov". Each token must hit either first or last name.
            name_q = models.Q()
            for token in name.split():
                name_q &= models.Q(first_name__icontains=token) | models.Q(last_name__icontains=token)
            qs = qs.filter(name_q)

        # Email lookup is scoped to authenticated shop owners — used by the
        # "Add barber" modal. Never exposed to anonymous callers to avoid
        # being used as an account-enumeration oracle.
        is_shop_owner = (
            request.user.is_authenticated
            and getattr(request.user, 'role', None) == CustomUser.Role.SHOP_OWNER
        )
        email = request.query_params.get('email')
        if email and is_shop_owner:
            qs = qs.filter(email__icontains=email)

        exclude_shop = request.query_params.get('exclude_shop')
        if exclude_shop:
            try:
                qs = qs.exclude(shop_memberships__shop_id=int(exclude_shop))
            except (ValueError, TypeError):
                pass

        qs = qs.order_by('first_name', 'last_name', 'id').distinct()
        serializer = BarberListItemSerializer(
            qs,
            many=True,
            context={
                'request': request,
                'include_email': is_shop_owner,
            },
        )
        return Response(serializer.data)
