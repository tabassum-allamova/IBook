from rest_framework import serializers
from .models import Service, WeeklySchedule, DateBlock


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price', 'duration_minutes', 'sort_order']
        read_only_fields = ['id']


class ServiceReorderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sort_order = serializers.IntegerField()


class WeeklyScheduleSerializer(serializers.ModelSerializer):
    # Accept 'weekday' as input, map to 'day_of_week' field
    weekday = serializers.IntegerField(source='day_of_week', required=False)

    class Meta:
        model = WeeklySchedule
        fields = ['id', 'weekday', 'day_of_week', 'is_working', 'start_time', 'end_time', 'break_start', 'break_end']
        read_only_fields = ['id']
        extra_kwargs = {
            'day_of_week': {'required': False},
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Include weekday in output (same as day_of_week) for compatibility
        ret['weekday'] = ret['day_of_week']
        return ret


class DateBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateBlock
        fields = ['id', 'date', 'block_start', 'block_end', 'reason']
        read_only_fields = ['id']
