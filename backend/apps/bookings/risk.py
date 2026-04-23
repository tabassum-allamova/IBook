"""
No-show risk scoring for upcoming appointments.

Why rule-based and not a trained ML model?
- The signal is dominated by the customer's own no-show history.
- A transparent weighted rule is defensible ('here are the six factors
  and their weights') in a way that a learned classifier isn't, and the
  barber using the badge in practice benefits from that explainability.
- Laplace smoothing handles the common case of a customer with zero or
  one past bookings, which would otherwise produce a noisy 0% or 100%
  rate.

The final score is a 0..1 number banded into Low / Medium / High. We
also surface up to three short 'why' tags so the UI can render the
reasoning next to the badge instead of asking the barber to trust a
black box.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional


# Laplace smoothing toward a 10% no-show / 10% cancellation prior. With
# no history a customer gets the baseline, not a noisy 0%. The sample
# size of 5 means it takes ~5 confirmed outcomes for the observed rate
# to dominate the prior.
_PRIOR_NOSHOW = 0.10
_PRIOR_CANCEL = 0.10
_PRIOR_SAMPLE = 5.0

# Weights sum to 1.0 so `score` is interpretable on [0, 1].
_W_NOSHOW = 0.55
_W_CANCEL = 0.15
_W_FIRST_TIME = 0.10
_W_WEEKDAY = 0.08
_W_TIME_OF_DAY = 0.07
_W_LEAD_TIME = 0.05

_BAND_MEDIUM = 0.25
_BAND_HIGH = 0.50


@dataclass
class CustomerStats:
    """Historical outcome counts for a single customer across all barbers.

    We count every terminal outcome — completed, cancelled, no-show —
    because what we're modelling is 'will this booking actually happen',
    and a cancellation is a weaker-but-still-relevant signal of that.
    """

    completed: int = 0
    cancelled: int = 0
    no_show: int = 0

    @property
    def total(self) -> int:
        return self.completed + self.cancelled + self.no_show

    def noshow_rate(self) -> float:
        return (self.no_show + _PRIOR_NOSHOW * _PRIOR_SAMPLE) / (self.total + _PRIOR_SAMPLE)

    def cancel_rate(self) -> float:
        return (self.cancelled + _PRIOR_CANCEL * _PRIOR_SAMPLE) / (self.total + _PRIOR_SAMPLE)


def _weekday_factor(d: date) -> float:
    # Loose prior: Mondays and Sundays skew slightly higher, Saturday
    # lowest. Calibrated to be a small nudge, not a strong signal.
    return {
        0: 0.40,  # Mon
        1: 0.35,  # Tue
        2: 0.30,  # Wed
        3: 0.30,  # Thu
        4: 0.25,  # Fri
        5: 0.20,  # Sat
        6: 0.35,  # Sun
    }[d.weekday()]


def _time_of_day_factor(t: time) -> float:
    h = t.hour
    if h < 9:
        return 0.55  # Very early — commuter/rushed, more cancellations
    if h < 12:
        return 0.20
    if h < 17:
        return 0.25
    if h < 20:
        return 0.30
    return 0.55  # Late evening — tiredness / plans change


def _lead_time_factor(created_at: datetime, appointment_at: datetime) -> float:
    # Normalise to naive datetimes before subtracting. `created_at` is
    # timezone-aware (Django default) while `datetime.combine(date, time)`
    # yields a naive value; the delta is meaningful to the minute either
    # way and we don't need absolute-timezone accuracy for risk banding.
    a = appointment_at.replace(tzinfo=None) if appointment_at.tzinfo else appointment_at
    c = created_at.replace(tzinfo=None) if created_at.tzinfo else created_at
    delta = a - c
    hours = delta.total_seconds() / 3600.0
    if hours < 24:
        return 0.45  # Short-notice — impulsive bookings cancel more
    if hours < 72:
        return 0.25
    if hours < 336:  # 14 days
        return 0.20
    return 0.45  # Booked far in advance — forgotten


def compute_risk(
    stats: CustomerStats,
    appointment_date: date,
    appointment_time: time,
    created_at: datetime,
    now: Optional[datetime] = None,
) -> dict:
    """Produce the risk payload the API returns for a single appointment.

    Returns:
        {
          'score': float in [0, 1],
          'band':  'low' | 'medium' | 'high',
          'factors': list[str]   # up to 3 short 'why' tags
        }
    """
    del now  # reserved for future use (e.g. hours-until-start decay)

    noshow_rate = stats.noshow_rate()
    cancel_rate = stats.cancel_rate()
    first_time = 1.0 if stats.total == 0 else 0.0
    weekday = _weekday_factor(appointment_date)
    tod = _time_of_day_factor(appointment_time)
    appointment_at = datetime.combine(appointment_date, appointment_time)
    lead = _lead_time_factor(created_at, appointment_at)

    score = (
        _W_NOSHOW * noshow_rate
        + _W_CANCEL * cancel_rate
        + _W_FIRST_TIME * first_time
        + _W_WEEKDAY * weekday
        + _W_TIME_OF_DAY * tod
        + _W_LEAD_TIME * lead
    )
    score = max(0.0, min(1.0, score))

    if score < _BAND_MEDIUM:
        band = 'low'
    elif score < _BAND_HIGH:
        band = 'medium'
    else:
        band = 'high'

    # Order factors by priority so the UI tags read as 'here's the
    # biggest thing, then the second, etc.'
    factors: list[str] = []
    if stats.no_show > 0:
        factors.append(
            f'{stats.no_show} past no-show' if stats.no_show == 1
            else f'{stats.no_show} past no-shows'
        )
    if first_time:
        factors.append('First-time customer')
    a_naive = appointment_at.replace(tzinfo=None) if appointment_at.tzinfo else appointment_at
    c_naive = created_at.replace(tzinfo=None) if created_at.tzinfo else created_at
    lead_hours = (a_naive - c_naive).total_seconds() / 3600.0
    if lead_hours < 24:
        factors.append('Booked within 24h')
    elif lead_hours > 336:
        factors.append('Booked >2 weeks out')
    if appointment_time.hour < 9 or appointment_time.hour >= 20:
        factors.append('Unusual hour')
    if stats.cancelled > 1:
        factors.append(f'{stats.cancelled} past cancellations')

    return {
        'score': round(score, 3),
        'band': band,
        'factors': factors[:3],
    }
