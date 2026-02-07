"""
Shops domain models.

Provides Shop, ShopHours, ShopPhoto, and BarberShopMembership models
for the barbershop management functionality (SHOP-01, SHOP-02).
"""

from django.db import models
from django.conf import settings


class Shop(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shop',
        limit_choices_to={'role': 'SHOP_OWNER'},
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShopHours(models.Model):
    DAYS = [(i, name) for i, name in enumerate(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )]
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='hours')
    day_of_week = models.SmallIntegerField(choices=DAYS)
    is_open = models.BooleanField(default=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = [('shop', 'day_of_week')]
        ordering = ['day_of_week']


class ShopPhoto(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='shops/photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class BarberShopMembership(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='memberships')
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shop_memberships',
        limit_choices_to={'role': 'BARBER'},
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('shop', 'barber')]
