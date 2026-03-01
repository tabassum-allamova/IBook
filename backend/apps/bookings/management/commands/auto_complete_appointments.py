"""
Management command to auto-complete past confirmed appointments.

Marks appointments as COMPLETED when:
- The appointment date is in the past (before today), OR
- The appointment is today but end_time has passed.

Usage:
    python manage.py auto_complete_appointments

Designed to be run via cron / scheduler, or inline during barber list views.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import Appointment


class Command(BaseCommand):
    help = 'Mark past CONFIRMED appointments as COMPLETED.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()

        # Past-date appointments
        past_count = Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            date__lt=today,
        ).update(status=Appointment.Status.COMPLETED)

        # Today's appointments whose end_time has passed
        today_count = Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            date=today,
            end_time__lte=now.time(),
        ).update(status=Appointment.Status.COMPLETED)

        total = past_count + today_count
        self.stdout.write(
            self.style.SUCCESS(f'Auto-completed {total} appointment(s).')
        )
