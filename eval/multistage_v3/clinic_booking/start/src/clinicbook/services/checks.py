"""Consistency checks on the bookings file, for after it has been edited by hand."""
from collections import Counter

from ..errors import NotFound


def _unknown(bookings, clinic):
    problems = []
    for booking in bookings:
        try:
            clinic.practitioner(booking.practitioner)
        except NotFound:
            problems.append(f"{booking.id}: unknown practitioner {booking.practitioner}")
        try:
            clinic.room(booking.room)
        except NotFound:
            problems.append(f"{booking.id}: unknown room {booking.room}")
    return problems


def _duplicates(bookings):
    counts = Counter(booking.id for booking in bookings)
    return [f"{booking_id}: used {count} times" for booking_id, count in sorted(counts.items()) if count > 1]


def _clashes(bookings):
    """Pairs of active bookings that share a practitioner or a room at the same time."""
    problems = []
    ordered = sorted(bookings, key=lambda b: (b.starts_at, b.id))
    for index, first in enumerate(ordered):
        for second in ordered[index + 1:]:
            if second.starts_at >= first.ends_at:
                break
            if not second.overlaps(first.day, first.start, first.minutes):
                continue
            if first.practitioner == second.practitioner:
                problems.append(f"{first.id} and {second.id}: {first.practitioner} booked twice at {second.start:%H:%M}")
            elif first.room == second.room:
                problems.append(f"{first.id} and {second.id}: room {first.room} booked twice at {second.start:%H:%M}")
    return problems


def problems(bookings, clinic):
    """Everything wrong with the bookings, one line each; an empty list means all is well."""
    return _duplicates(bookings) + _unknown(bookings, clinic) + _clashes(bookings)
