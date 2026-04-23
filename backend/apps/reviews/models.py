from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    appointment = models.OneToOneField(
        'bookings.Appointment',
        on_delete=models.CASCADE,
        related_name='review',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
    )
    rating = models.PositiveSmallIntegerField(
        help_text='1–5 star rating',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['barber', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='review_rating_1_to_5',
            ),
        ]

    def __str__(self):
        return f'Review by {self.reviewer} for {self.barber} — {self.rating}★'


class ReviewService(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='service_ratings',
    )
    service_name = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField(
        help_text='1–5 star rating',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='review_service_rating_1_to_5',
            ),
        ]

    def __str__(self):
        return f'{self.service_name} — {self.rating}★'
