from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsBarber
from .models import Service, WeeklySchedule, DateBlock
from .serializers import (
    ServiceSerializer,
    ServiceReorderSerializer,
    WeeklyScheduleSerializer,
    DateBlockSerializer,
)


class ServiceListCreateView(APIView):
    permission_classes = [IsBarber]

    def get(self, request: Request) -> Response:
        services = Service.objects.filter(barber=request.user)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(barber=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ServiceDetailView(APIView):
    permission_classes = [IsBarber]

    def _get_service(self, request, pk):
        try:
            return Service.objects.get(pk=pk, barber=request.user)
        except Service.DoesNotExist:
            return None

    def patch(self, request: Request, pk: int) -> Response:
        service = self._get_service(request, pk)
        if not service:
            return Response({'detail': 'Service not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pk: int) -> Response:
        service = self._get_service(request, pk)
        if not service:
            return Response({'detail': 'Service not found.'}, status=status.HTTP_404_NOT_FOUND)
        service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceReorderView(APIView):
    permission_classes = [IsBarber]

    def patch(self, request: Request) -> Response:
        items = request.data
        if not isinstance(items, list):
            return Response(
                {'detail': 'Expected a list of {id, sort_order} objects.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ServiceReorderSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            for item in serializer.validated_data:
                Service.objects.filter(
                    id=item['id'],
                    barber=request.user,
                ).update(sort_order=item['sort_order'])

        return Response({'detail': 'Reordered successfully.'}, status=status.HTTP_200_OK)


class WeeklyScheduleView(APIView):
    permission_classes = [IsBarber]

    def _ensure_all_days(self, barber) -> None:
        existing_days = set(
            WeeklySchedule.objects.filter(barber=barber).values_list('day_of_week', flat=True)
        )
        missing = [day for day in range(7) if day not in existing_days]
        if missing:
            WeeklySchedule.objects.bulk_create([
                WeeklySchedule(barber=barber, day_of_week=day)
                for day in missing
            ])

    def get(self, request: Request) -> Response:
        self._ensure_all_days(request.user)
        schedule = WeeklySchedule.objects.filter(barber=request.user).order_by('day_of_week')
        serializer = WeeklyScheduleSerializer(schedule, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request) -> Response:
        rows = request.data
        if not isinstance(rows, list):
            return Response(
                {'detail': 'Expected a list of schedule rows.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = []
        with transaction.atomic():
            for row in rows:
                day = row.get('weekday') if row.get('weekday') is not None else row.get('day_of_week')
                if day is None:
                    return Response(
                        {'detail': "Each row must include 'weekday' or 'day_of_week'."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                defaults = {
                    'is_working': row.get('is_working', False),
                    'start_time': row.get('start_time'),
                    'end_time': row.get('end_time'),
                    'break_start': row.get('break_start'),
                    'break_end': row.get('break_end'),
                }
                obj, _ = WeeklySchedule.objects.update_or_create(
                    barber=request.user,
                    day_of_week=day,
                    defaults=defaults,
                )
                result.append(obj)

        serializer = WeeklyScheduleSerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DateBlockListCreateView(APIView):
    permission_classes = [IsBarber]

    def get(self, request: Request) -> Response:
        blocks = DateBlock.objects.filter(barber=request.user)
        serializer = DateBlockSerializer(blocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = DateBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(barber=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DateBlockDetailView(APIView):
    permission_classes = [IsBarber]

    def delete(self, request: Request, pk: int) -> Response:
        try:
            block = DateBlock.objects.get(pk=pk, barber=request.user)
        except DateBlock.DoesNotExist:
            return Response(
                {'detail': 'Date block not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
