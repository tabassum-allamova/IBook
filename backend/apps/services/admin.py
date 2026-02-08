from django.contrib import admin
from .models import Service, WeeklySchedule, DateBlock


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'barber', 'price', 'duration_minutes', 'sort_order']
    list_filter = ['barber']
    ordering = ['sort_order']


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = ['barber', 'day_of_week', 'is_working', 'start_time', 'end_time']
    list_filter = ['barber', 'is_working']


@admin.register(DateBlock)
class DateBlockAdmin(admin.ModelAdmin):
    list_display = ['barber', 'date', 'block_start', 'block_end', 'reason']
    list_filter = ['barber']
