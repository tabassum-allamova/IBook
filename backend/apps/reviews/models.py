"""
Reviews models.

Review       — one review per appointment (OneToOneField enforces DB constraint)
ReviewService — per-service rating snapshot linked to a Review
"""

from django.conf import settings
from django.db import models


class Review(models.Model):
    """Customer review for a completed appointment."""

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
    rating = models.PositiveSmallIntegerField(help_text='1–5 star rating')
    text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['barber', 'created_at']),
        ]

    def __str__(self):
        return f'Review by {self.reviewer} for {self.barber} — {self.rating}★'


class ReviewService(models.Model):
    """Per-service rating within a review (optional breakdown)."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='service_ratings',
    )
    service_name = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField(help_text='1–5 star rating')

    def __str__(self):
        return f'{self.service_name} — {self.rating}★'
