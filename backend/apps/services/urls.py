"""
Services app URL patterns.

Registers two groups (included from config/urls.py):
  api/services/       — service catalog endpoints
  api/availability/   — weekly schedule and date block endpoints
"""

from django.urls import path
from .views import (
    ServiceListCreateView,
    ServiceReorderView,
    WeeklyScheduleView,
    DateBlockListCreateView,
    DateBlockDetailView,
)

# Patterns under api/services/
services_urlpatterns = [
    path('reorder/', ServiceReorderView.as_view(), name='service-reorder'),
    path('', ServiceListCreateView.as_view(), name='service-list-create'),
]

# Patterns under api/availability/
availability_urlpatterns = [
    path('schedule/', WeeklyScheduleView.as_view(), name='weekly-schedule'),
    path('blocks/', DateBlockListCreateView.as_view(), name='date-block-list-create'),
    path('blocks/<int:pk>/', DateBlockDetailView.as_view(), name='date-block-detail'),
]
