"""Bookings caught by a closure added after they were made.

When the clinic file gains a closure or the holiday table changes, some booked
patients have to be phoned and moved. This finds them.
"""
from ..model.booking import BOOKED


def stranded(bookings, clinic, first, last):
    """Bookings still on from `first` to `last` that fall on a day the clinic is shut,
    or with a practitioner who no longer works that weekday."""
    found = []
    for booking in sorted(bookings, key=lambda b: (b.starts_at, b.id)):
        if booking.status != BOOKED or not first <= booking.day <= last:
            continue
        reason = clinic.hours.closed_reason(booking.day)
        if reason is None and not clinic.practitioner(booking.practitioner).works_on(booking.day):
            reason = f"{clinic.practitioner_name(booking.practitioner)} no longer works {booking.day:%A}s"
        if reason is not None:
            found.append((booking, reason))
    return found
