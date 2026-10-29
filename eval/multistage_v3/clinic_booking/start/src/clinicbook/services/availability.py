"""Free slots: when each practitioner could still see a patient."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..model.times import from_minutes, minutes_of


@dataclass(frozen=True)
class Slot:
    practitioner: str
    room: str
    day: date
    start: time
    minutes: int


def slot_starts(opens, closes, minutes):
    """Start times of the whole slots between opening and closing, back to back."""
    starts = []
    current = minutes_of(opens)
    while current + minutes <= minutes_of(closes):
        starts.append(from_minutes(current))
        current += minutes
    return starts


def _clashes(bookings, practitioner, day, start, minutes):
    return any(
        booking.overlaps(day, start, minutes)
        and (booking.practitioner == practitioner.id or booking.room == practitioner.room)
        for booking in bookings
    )


def free_slots(clinic, bookings, day, now, practitioner=None):
    """Slots still free on `day`, practitioner by practitioner, earliest first.

    Slots that start before `now` or beyond the booking horizon are left out,
    since the desk would refuse them.
    """
    settings = clinic.settings
    if (day - now.date()).days > settings.booking_horizon_days:
        return []
    window = clinic.hours.window(day)
    if window is None:
        return []
    minutes = settings.slot_minutes
    starts = slot_starts(*window, minutes)
    slots = []
    for who in clinic.working_on(day):
        if practitioner is not None and who.id != practitioner:
            continue
        for start in starts:
            if datetime.combine(day, start) < now:
                continue
            if _clashes(bookings, who, day, start, minutes):
                continue
            slots.append(Slot(who.id, who.room, day, start, minutes))
    return slots


def free_slots_from(clinic, bookings, first, days, now, practitioner=None):
    """Free slots over `days` days starting with `first`."""
    found = []
    for offset in range(days):
        found.extend(free_slots(clinic, bookings, first + timedelta(days=offset), now, practitioner))
    return found


def first_free(clinic, bookings, first, days, now, practitioner=None):
    """The earliest free slot in the period, or None."""
    slots = free_slots_from(clinic, bookings, first, days, now, practitioner)
    return min(slots, key=lambda slot: (slot.day, slot.start), default=None)
