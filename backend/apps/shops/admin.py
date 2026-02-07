from django.contrib import admin

from .models import BarberShopMembership, Shop, ShopHours, ShopPhoto

admin.site.register(Shop)
admin.site.register(ShopHours)
admin.site.register(ShopPhoto)
admin.site.register(BarberShopMembership)
