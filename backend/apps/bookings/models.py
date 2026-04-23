from django.db import models
from django.conf import settings


class Appointment(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'

    class PaymentMethod(models.TextChoices):
        ONLINE = 'ONLINE', 'Pay Online'
        AT_SHOP = 'AT_SHOP', 'Pay at Shop'

    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PENDING = 'PENDING', 'Pending'
        DECLINED = 'DECLINED', 'Declined'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_appointments',
        limit_choices_to={'role': 'CUSTOMER'},
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='barber_appointments',
        limit_choices_to={'role': 'BARBER'},
    )
    services = models.ManyToManyField(
        'services.Service',
        through='AppointmentService',
        related_name='appointments',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    total_price = models.PositiveIntegerField(
        help_text='Total in UZS, snapshotted at booking time',
    )
    total_duration = models.PositiveSmallIntegerField(
        help_text='Total minutes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['barber', 'date', 'status']),
            models.Index(fields=['customer', 'status']),
        ]
        constraints = [
            # No two CONFIRMED appointments can share the same (barber, date,
            # start_time). `select_for_update` is a no-op on SQLite so this
            # is the real defence against double-booking under concurrency.
            models.UniqueConstraint(
                fields=['barber', 'date', 'start_time'],
                condition=models.Q(status='CONFIRMED'),
                name='unique_confirmed_slot_per_barber',
            ),
        ]

    def __str__(self):
        return f'{self.customer} -> {self.barber} on {self.date} {self.start_time}'


class AppointmentService(models.Model):
    """Snapshots service info at booking time."""

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='appointment_services',
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
    )
    service_name = models.CharField(max_length=200)
    service_price = models.PositiveIntegerField()
    service_duration = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.service_name} ({self.service_duration}min)'
