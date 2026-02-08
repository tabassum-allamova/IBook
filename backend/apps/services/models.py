from django.db import models
from django.conf import settings


class Service(models.Model):
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        limit_choices_to={'role': 'BARBER'},
    )
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField(help_text='Price in UZS (Uzbek som)')
    duration_minutes = models.PositiveSmallIntegerField(
        help_text='Duration in minutes, multiples of 15'
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name} ({self.barber})"


class WeeklySchedule(models.Model):
    DAYS = [(i, name) for i, name in enumerate(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )]
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weekly_schedule',
    )
    day_of_week = models.SmallIntegerField(choices=DAYS)
    is_working = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = [('barber', 'day_of_week')]
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.barber} - Day {self.day_of_week}"


class DateBlock(models.Model):
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='date_blocks',
    )
    date = models.DateField()
    block_start = models.TimeField(null=True, blank=True)
    block_end = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['date', 'block_start']

    def __str__(self):
        return f"{self.barber} blocked {self.date}"
