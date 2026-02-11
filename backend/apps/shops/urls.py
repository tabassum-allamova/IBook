"""
URL patterns for the shops app.

Order matters: 'my/' must come before '<int:shop_id>/' to avoid integer parse clash.
"""

from django.urls import path

from .views import MembershipView, ShopCreateView, ShopDetailView, ShopHoursView, ShopMeView, ShopPhotoView

urlpatterns = [
    # Owner self-lookup — must come before parameterised routes
    path('my/', ShopMeView.as_view(), name='shop-me'),

    # Shop creation and listing
    path('', ShopCreateView.as_view(), name='shop-create'),

    # Shop detail and update
    path('<int:shop_id>/', ShopDetailView.as_view(), name='shop-detail'),

    # Operating hours
    path('<int:shop_id>/hours/', ShopHoursView.as_view(), name='shop-hours'),

    # Photos
    path('<int:shop_id>/photos/', ShopPhotoView.as_view(), name='shop-photos'),
    path('<int:shop_id>/photos/<int:photo_id>/', ShopPhotoView.as_view(), name='shop-photo-detail'),

    # Barber memberships
    path('<int:shop_id>/members/', MembershipView.as_view(), name='shop-members'),
    path('<int:shop_id>/members/<int:barber_id>/', MembershipView.as_view(), name='shop-member-detail'),
]
