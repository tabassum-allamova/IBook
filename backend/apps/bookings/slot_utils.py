from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple


def compute_available_slots(
    schedule_start: Optional[time],
    schedule_end: Optional[time],
    break_start: Optional[time],
    break_end: Optional[time],
    is_working: bool,
    block_ranges: List[Tuple[time, time]],
    booked_ranges: List[Tuple[time, time]],
    duration_minutes: int,
    slot_interval: int = 15,
) -> List[str]:
    """Return available start times as HH:MM strings."""
    if not is_working or not schedule_start or not schedule_end:
        return []

    slots: List[str] = []
    current = datetime.combine(date.today(), schedule_start)
    end_limit = datetime.combine(date.today(), schedule_end) - timedelta(
        minutes=duration_minutes,
    )

    while current <= end_limit:
        candidate_start = current.time()
        candidate_end = (current + timedelta(minutes=duration_minutes)).time()

        if break_start and break_end:
            if _overlaps(candidate_start, candidate_end, break_start, break_end):
                current += timedelta(minutes=slot_interval)
                continue

        blocked = False
        for block_s, block_e in block_ranges:
            if _overlaps(candidate_start, candidate_end, block_s, block_e):
                blocked = True
                break
        if blocked:
            current += timedelta(minutes=slot_interval)
            continue

        booked = False
        for book_s, book_e in booked_ranges:
            if _overlaps(candidate_start, candidate_end, book_s, book_e):
                booked = True
                break
        if booked:
            current += timedelta(minutes=slot_interval)
            continue

        slots.append(candidate_start.strftime('%H:%M'))
        current += timedelta(minutes=slot_interval)

    return slots


def _overlaps(start1: time, end1: time, start2: time, end2: time) -> bool:
    return start1 < end2 and start2 < end1
