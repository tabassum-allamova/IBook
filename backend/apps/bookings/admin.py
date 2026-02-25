from django.contrib import admin

from .models import Appointment, AppointmentService


class AppointmentServiceInline(admin.TabularInline):
    model = AppointmentService
    extra = 0
    readonly_fields = ('service_name', 'service_price', 'service_duration')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'barber',
        'date',
        'start_time',
        'end_time',
        'status',
        'payment_status',
        'total_price',
    )
    list_filter = ('status', 'payment_status', 'payment_method', 'date')
    search_fields = ('customer__email', 'barber__email')
    date_hierarchy = 'date'
    inlines = [AppointmentServiceInline]


@admin.register(AppointmentService)
class AppointmentServiceAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'service_name', 'service_price', 'service_duration')
