"""
DRF API views for the shops domain.

Endpoints:
    POST   /api/shops/                         — ShopCreateView
    GET    /api/shops/my/                      — ShopMeView
    GET    /api/shops/<shop_id>/               — ShopDetailView
    PATCH  /api/shops/<shop_id>/               — ShopDetailView
    PUT    /api/shops/<shop_id>/hours/         — ShopHoursView
    POST   /api/shops/<shop_id>/photos/        — ShopPhotoView
    DELETE /api/shops/<shop_id>/photos/<id>/   — ShopPhotoView
    POST   /api/shops/<shop_id>/members/       — MembershipView
    DELETE /api/shops/<shop_id>/members/<id>/  — MembershipView
"""

from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import CustomUser
from apps.users.permissions import IsShopOwner

from .models import BarberShopMembership, Shop, ShopHours, ShopPhoto
from .serializers import MembershipSerializer, ShopHoursSerializer, ShopPhotoSerializer, ShopSerializer


class ShopCreateView(APIView):
    """POST /api/shops/ — create a new shop for the authenticated owner."""

    permission_classes = [IsShopOwner]

    def post(self, request):
        serializer = ShopSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)


class ShopMeView(APIView):
    """GET /api/shops/my/ — return the shop owned by the authenticated user."""

    permission_classes = [IsShopOwner]

    def get(self, request):
        try:
            shop = request.user.shop  # OneToOneField reverse accessor
        except Shop.DoesNotExist:
            return Response({'detail': 'No shop found.'}, status=404)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)


class ShopDetailView(APIView):
    """
    GET  /api/shops/<shop_id>/ — retrieve shop detail (any authenticated user).
    PATCH /api/shops/<shop_id>/ — update shop (owner only, object-level check).
    """

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsShopOwner()]
        return [IsAuthenticated()]

    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def patch(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        serializer = ShopSerializer(shop, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ShopHoursView(APIView):
    """PUT /api/shops/<shop_id>/hours/ — bulk-upsert operating hours."""

    permission_classes = [IsShopOwner]

    def put(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)

        rows = request.data if isinstance(request.data, list) else request.data.get('hours', [])
        updated = []
        for row in rows:
            serializer = ShopHoursSerializer(data=row)
            serializer.is_valid(raise_exception=True)
            obj, _ = ShopHours.objects.update_or_create(
                shop=shop,
                day_of_week=serializer.validated_data['day_of_week'],
                defaults={k: v for k, v in serializer.validated_data.items() if k != 'day_of_week'},
            )
            updated.append(obj)
        return Response(ShopHoursSerializer(updated, many=True).data)


class ShopPhotoView(APIView):
    """
    POST   /api/shops/<shop_id>/photos/           — upload photo (max 5).
    DELETE /api/shops/<shop_id>/photos/<photo_id>/ — delete photo.
    """

    permission_classes = [IsShopOwner]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        if shop.photos.count() >= 5:
            return Response({'error': 'Max 5 photos allowed per shop.'}, status=400)
        serializer = ShopPhotoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(shop=shop)
        return Response(serializer.data, status=201)

    def delete(self, request, shop_id, photo_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        photo = get_object_or_404(ShopPhoto, pk=photo_id, shop=shop)
        photo.delete()
        return Response(status=204)


class MembershipView(APIView):
    """
    POST   /api/shops/<shop_id>/members/              — add a barber.
    DELETE /api/shops/<shop_id>/members/<barber_id>/  — remove a barber.
    """

    permission_classes = [IsShopOwner]

    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        barber_id = request.data.get('barber_id')
        barber = get_object_or_404(CustomUser, pk=barber_id, role=CustomUser.Role.BARBER)
        membership, created = BarberShopMembership.objects.get_or_create(shop=shop, barber=barber)
        if not created:
            return Response({'detail': 'Barber already a member.'}, status=400)
        serializer = MembershipSerializer(membership)
        return Response(serializer.data, status=201)

    def delete(self, request, shop_id, barber_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        membership = get_object_or_404(BarberShopMembership, shop=shop, barber_id=barber_id)
        membership.delete()
        return Response(status=204)
