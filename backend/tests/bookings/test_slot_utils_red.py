"""
RED phase tests for slot computation pure function.
These tests verify the behavior of compute_available_slots and _overlaps.
"""

from datetime import time

import pytest

from apps.bookings.slot_utils import compute_available_slots, _overlaps


class TestOverlaps:
    """Tests for the _overlaps helper."""

    def test_overlapping_intervals(self):
        assert _overlaps(time(9, 0), time(10, 0), time(9, 30), time(10, 30)) is True

    def test_non_overlapping_intervals(self):
        assert _overlaps(time(9, 0), time(10, 0), time(10, 0), time(11, 0)) is False

    def test_contained_interval(self):
        assert _overlaps(time(9, 0), time(12, 0), time(10, 0), time(11, 0)) is True


class TestComputeAvailableSlots:
    """Tests for compute_available_slots pure function."""

    def test_non_working_day_returns_empty(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(18, 0),
            break_start=None,
            break_end=None,
            is_working=False,
            block_ranges=[],
            booked_ranges=[],
            duration_minutes=30,
        )
        assert result == []

    def test_no_schedule_times_returns_empty(self):
        result = compute_available_slots(
            schedule_start=None,
            schedule_end=None,
            break_start=None,
            break_end=None,
            is_working=True,
            block_ranges=[],
            booked_ranges=[],
            duration_minutes=30,
        )
        assert result == []

    def test_basic_slots_9_to_12(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(12, 0),
            break_start=None,
            break_end=None,
            is_working=True,
            block_ranges=[],
            booked_ranges=[],
            duration_minutes=30,
        )
        expected = [
            '09:00', '09:15', '09:30', '09:45',
            '10:00', '10:15', '10:30', '10:45',
            '11:00', '11:15', '11:30',
        ]
        assert result == expected

    def test_slots_exclude_break(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(18, 0),
            break_start=time(13, 0),
            break_end=time(14, 0),
            is_working=True,
            block_ranges=[],
            booked_ranges=[],
            duration_minutes=30,
        )
        # No slot should overlap with 13:00-14:00
        for slot in result:
            h, m = map(int, slot.split(':'))
            slot_start = time(h, m)
            slot_end_minutes = h * 60 + m + 30
            slot_end = time(slot_end_minutes // 60, slot_end_minutes % 60)
            assert not _overlaps(slot_start, slot_end, time(13, 0), time(14, 0)), \
                f"Slot {slot} overlaps break period"

    def test_slots_exclude_booked(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(12, 0),
            break_start=None,
            break_end=None,
            is_working=True,
            block_ranges=[],
            booked_ranges=[(time(10, 0), time(10, 30))],
            duration_minutes=30,
        )
        assert '10:00' not in result
        assert '10:15' not in result
        assert '09:00' in result
        assert '10:30' in result

    def test_slots_exclude_block(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(18, 0),
            break_start=None,
            break_end=None,
            is_working=True,
            block_ranges=[(time(15, 0), time(16, 0))],
            booked_ranges=[],
            duration_minutes=30,
        )
        # No slot should overlap with 15:00-16:00
        for slot in result:
            h, m = map(int, slot.split(':'))
            slot_start = time(h, m)
            slot_end_minutes = h * 60 + m + 30
            slot_end = time(slot_end_minutes // 60, slot_end_minutes % 60)
            assert not _overlaps(slot_start, slot_end, time(15, 0), time(16, 0)), \
                f"Slot {slot} overlaps block range"

    def test_long_duration_spanning_break_rejected(self):
        result = compute_available_slots(
            schedule_start=time(9, 0),
            schedule_end=time(18, 0),
            break_start=time(13, 0),
            break_end=time(14, 0),
            is_working=True,
            block_ranges=[],
            booked_ranges=[],
            duration_minutes=90,
        )
        # Slot at 12:30 would run 12:30-14:00 overlapping break
        assert '12:30' not in result
        # Slot at 12:00 would run 12:00-13:30 overlapping break
        assert '12:00' not in result
        # Slot at 11:30 would run 11:30-13:00 which ends at break start, should be OK
        assert '11:30' in result
