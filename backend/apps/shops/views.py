from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import CustomUser
from apps.users.permissions import IsShopOwner

from .models import BarberShopMembership, Shop, ShopHours, ShopPhoto
from .serializers import MembershipSerializer, ShopHoursSerializer, ShopListSerializer, ShopPhotoSerializer, ShopSerializer
from .utils import annotate_distance


class ShopListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = Shop.objects.all()

        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        lat_param = request.query_params.get('lat')
        lng_param = request.query_params.get('lng')

        if lat_param is not None and lng_param is not None:
            try:
                lat = float(lat_param)
                lng = float(lng_param)
            except (ValueError, TypeError):
                return Response({'detail': 'lat and lng must be valid floating-point numbers.'}, status=400)
            queryset = annotate_distance(queryset, lat, lng)

        serializer = ShopListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        from apps.users.permissions import IsShopOwner as _IsShopOwner
        permission = _IsShopOwner()
        if not permission.has_permission(request, self):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        serializer = ShopSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)


class ShopCreateView(APIView):
    permission_classes = [IsShopOwner]

    def post(self, request):
        serializer = ShopSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)


class ShopMeView(APIView):
    permission_classes = [IsShopOwner]

    def get(self, request):
        try:
            shop = request.user.shop  # OneToOneField reverse accessor
        except Shop.DoesNotExist:
            return Response({'detail': 'No shop found.'}, status=404)
        serializer = ShopSerializer(shop, context={'request': request})
        return Response(serializer.data)


class ShopDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsShopOwner()]
        return [AllowAny()]

    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        serializer = ShopSerializer(shop, context={'request': request})
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
    permission_classes = [IsShopOwner]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, shop_id):
        files = request.FILES.getlist('image')
        if not files:
            return Response({'error': 'No image files provided.'}, status=400)

        # Lock the shop row so two concurrent uploads can't both pass the
        # 5-photo cap. Count + create happen inside the same transaction.
        with transaction.atomic():
            shop = Shop.objects.select_for_update().filter(pk=shop_id).first()
            if shop is None:
                return Response({'detail': 'Shop not found.'}, status=404)
            if shop.owner_id != request.user.id:
                return Response({'detail': 'You do not own this shop.'}, status=403)
            current_count = shop.photos.count()
            if current_count + len(files) > 5:
                return Response(
                    {'error': f'Max 5 photos. You have {current_count}, trying to add {len(files)}.'},
                    status=400,
                )
            created = [ShopPhoto.objects.create(shop=shop, image=f) for f in files]

        serializer = ShopPhotoSerializer(created, many=True, context={'request': request})
        return Response(serializer.data, status=201)

    def delete(self, request, shop_id, photo_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if shop.owner != request.user:
            return Response({'detail': 'You do not own this shop.'}, status=403)
        photo = get_object_or_404(ShopPhoto, pk=photo_id, shop=shop)
        photo.delete()
        return Response(status=204)


class MembershipView(APIView):
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
