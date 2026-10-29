"""Booking references: `B` followed by a running number, `B0001`, `B0002`, ..."""

PREFIX = "B"
WIDTH = 4


def booking_number(booking_id):
    if not booking_id.startswith(PREFIX) or not booking_id[len(PREFIX):].isdigit():
        raise ValueError(f"not a booking reference: {booking_id!r}")
    return int(booking_id[len(PREFIX):])


def format_booking_id(number):
    return f"{PREFIX}{number:0{WIDTH}d}"


def next_booking_id(bookings):
    """One past the highest reference in use; references are never reused."""
    highest = max((booking_number(booking.id) for booking in bookings), default=0)
    return format_booking_id(highest + 1)
