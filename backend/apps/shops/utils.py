"""
Utility helpers for the shops app.

Provides:
  - annotate_distance: Haversine ORM annotation for distance calculation
"""

from django.db.models import ExpressionWrapper, FloatField, F
from django.db.models.functions import Cos, ASin, Sqrt, Radians

EARTH_DIAMETER_KM = 12742.0


def annotate_distance(queryset, lat: float, lng: float):
    """
    Annotate queryset with haversine_distance in km.

    Works on SQLite (Python 3.10+ with math functions enabled) and PostgreSQL.
    Filters out shops with null lat/lng before annotating.
    Returns queryset ordered by haversine_distance ascending.

    Args:
        queryset: Shop queryset
        lat: User latitude in decimal degrees
        lng: User longitude in decimal degrees

    Returns:
        Annotated and ordered queryset with haversine_distance field
    """
    # Pre-convert query point coords to radians in Python (constants, not DB fields)
    lat_r = lat * 0.017453292519943295  # pi/180
    lng_r = lng * 0.017453292519943295

    lat2 = Radians(F('lat'))
    lng2 = Radians(F('lng'))

    haversine = (
        0.5
        - Cos(lat2 - lat_r) / 2
        + Cos(lat_r) * Cos(lat2) * (1 - Cos(lng2 - lng_r)) / 2
    )
    distance = ExpressionWrapper(
        EARTH_DIAMETER_KM * ASin(Sqrt(haversine)),
        output_field=FloatField(),
    )
    return (
        queryset
        .filter(lat__isnull=False, lng__isnull=False)
        .annotate(haversine_distance=distance)
        .order_by('haversine_distance')
    )
