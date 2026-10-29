"""End-of-day summary for the practice manager."""
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..model.booking import NO_SHOW


@dataclass(frozen=True)
class DaySummary:
    day: date
    counts: dict
    fees_due: Decimal
    seen_by: dict

    @property
    def appointments(self):
        return sum(self.counts.values())


def day_summary(bookings, clinic, day):
    """Bookings on `day` by status, appointments per practitioner and no-show fees due."""
    todays = [booking for booking in bookings if booking.day == day]
    counts = Counter(booking.status for booking in todays)
    seen_by = Counter(clinic.practitioner_name(booking.practitioner) for booking in todays if booking.active)
    fees_due = clinic.settings.no_show_fee * counts[NO_SHOW]
    return DaySummary(day, dict(counts), fees_due, dict(seen_by))


def render_summary(summary, clinic):
    lines = [f"Summary for {summary.day:%A %d %B %Y}", f"Bookings: {summary.appointments}"]
    for status, number in sorted(summary.counts.items()):
        lines.append(f"  {status}: {number}")
    if summary.seen_by:
        lines.append("By practitioner:")
        for name, number in sorted(summary.seen_by.items()):
            lines.append(f"  {name}: {number}")
    lines.append(f"Fees due: {clinic.settings.money(summary.fees_due)}")
    return lines
