"""A course of treatment: the same time with the same practitioner, week after week."""
from datetime import timedelta

from ..errors import BookingError

LONGEST_COURSE = 12


def book_series(desk, practitioner, first_day, start, weeks, patient, phone):
    """Book `weeks` weekly appointments, or none at all.

    If any week cannot be booked, the weeks already booked are taken back out
    and the error names the week that failed.
    """
    if not 1 <= weeks <= LONGEST_COURSE:
        raise BookingError(f"a course runs for 1 to {LONGEST_COURSE} weeks")
    if weeks == 1:
        return [desk.book(practitioner, first_day, start, patient, phone)]
    made = []
    try:
        for week in range(weeks):
            day = first_day + timedelta(weeks=week)
            try:
                made.append(desk.book(practitioner, day, start, patient, phone))
            except BookingError as error:
                raise BookingError(f"week {week + 1} ({day}): {error}") from None
    except BookingError:
        for booking in made:
            desk.bookings.remove(booking)
        raise
    return made
