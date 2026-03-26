"""
Reviews serializers.

ReviewCreateSerializer  — validates POST /api/reviews/ input
ReviewListItemSerializer — formats a single review for GET /api/reviews/barber/<pk>/
"""

from rest_framework import serializers


class ReviewCreateSerializer(serializers.Serializer):
    """Validates input for creating a review."""

    appointment_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, allow_blank=True, default='')
    service_ratings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class ReviewListItemSerializer(serializers.Serializer):
    """Read-only representation of a review in list responses."""

    reviewer = serializers.SerializerMethodField()
    rating = serializers.IntegerField()
    text = serializers.CharField()
    date = serializers.SerializerMethodField()

    def get_reviewer(self, obj) -> str:
        """Format reviewer name as 'FirstName L.' or just 'FirstName'."""
        first = obj.reviewer.first_name or obj.reviewer.email.split('@')[0]
        last = obj.reviewer.last_name
        if last:
            return f'{first} {last[0]}.'
        return first

    def get_date(self, obj) -> str:
        return obj.created_at.date().isoformat()
