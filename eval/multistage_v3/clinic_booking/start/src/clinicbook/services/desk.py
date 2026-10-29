"""The front desk: taking bookings and recording what happened to them."""
from datetime import datetime

from ..errors import BookingError, NotFound
from ..model.booking import ATTENDED, BOOKED, CANCELLED, NO_SHOW, Booking
from ..model.times import minutes_between
from ..storage.ids import next_booking_id
from .validation import check_name, check_phone


class Desk:
    """Works on a list of bookings in place; saving them is the caller's job."""

    def __init__(self, clinic, bookings, clock):
        self.clinic = clinic
        self.bookings = bookings
        self.clock = clock

    def find(self, booking_id):
        for booking in self.bookings:
            if booking.id == booking_id:
                return booking
        raise NotFound(f"no booking {booking_id}")

    def book(self, practitioner, day, start, patient, phone):
        """Book `patient` with `practitioner` at `start` on `day` for one slot."""
        patient = check_name(patient)
        phone = check_phone(phone)
        who = self.clinic.practitioner(practitioner)
        self._check_when(who, day, start)
        minutes = self.clinic.settings.slot_minutes
        for other in self.bookings:
            if not other.overlaps(day, start, minutes):
                continue
            if other.practitioner == who.id:
                raise BookingError(f"{who.name} is already booked at {start:%H:%M}")
            if other.room == who.room:
                raise BookingError(f"room {who.room} is already booked at {start:%H:%M}")
        booking = Booking(
            id=next_booking_id(self.bookings),
            patient=patient,
            phone=phone,
            practitioner=who.id,
            room=who.room,
            day=day,
            start=start,
            minutes=minutes,
            created=self.clock.now(),
        )
        self.bookings.append(booking)
        return booking

    def _check_when(self, who, day, start):
        rules = self.clinic.settings
        now = self.clock.now()
        if datetime.combine(day, start) < now:
            raise BookingError("cannot book in the past")
        if (day - now.date()).days > rules.booking_horizon_days:
            raise BookingError(f"bookings open {rules.booking_horizon_days} days ahead")
        window = self.clinic.hours.window(day)
        if window is None:
            raise BookingError(f"clinic is closed on {day}")
        if not who.works_on(day):
            raise BookingError(f"{who.name} does not work on {day:%A}s")
        opens, closes = window
        offset = minutes_between(opens, start)
        if offset < 0 or offset + rules.slot_minutes > minutes_between(opens, closes):
            raise BookingError(f"{start:%H:%M} is outside opening hours")
        # Slots run back to back from opening time, so a booking has to start on one.
        if offset % rules.slot_minutes:
            raise BookingError(f"{start:%H:%M} is not a slot start")

    def _still_booked(self, booking_id):
        booking = self.find(booking_id)
        if booking.status != BOOKED:
            raise BookingError(f"booking {booking_id} is {booking.status}")
        return booking

    def _started(self, booking):
        if booking.starts_at > self.clock.now():
            raise BookingError(f"booking {booking.id} has not started yet")

    def cancel(self, booking_id):
        booking = self._still_booked(booking_id)
        booking.status = CANCELLED
        return booking

    def mark_attended(self, booking_id):
        booking = self._still_booked(booking_id)
        self._started(booking)
        booking.status = ATTENDED
        return booking

    def mark_no_show(self, booking_id):
        booking = self._still_booked(booking_id)
        self._started(booking)
        booking.status = NO_SHOW
        return booking

    def patient_bookings(self, phone):
        """Every booking made with this phone number, earliest first."""
        phone = check_phone(phone)
        return sorted((b for b in self.bookings if b.phone == phone), key=lambda b: b.starts_at)
