"""Taking, changing and cancelling reservations."""
from ..errors import InvalidState, Unavailable, ValidationError
from ..model.reservations import BOOKED, CANCELLED, IN_HOUSE, NO_SHOW, Reservation
from . import inventory, pricing
from .stay_rules import check_stay

DEFAULT_PLAN = "BAR"


def _next_id(hotel):
    return f"R{len(hotel.reservations) + 1:04d}"


def _check_free(hotel, room_type, arrival, departure, excluding=None):
    night = inventory.first_full_night(hotel, room_type, arrival, departure, excluding)
    if night is not None:
        raise Unavailable(f"No {room_type} rooms available on {night.isoformat()}")


def book(hotel, settings, *, guest, room_type, arrival, departure, adults=1, rate_plan=DEFAULT_PLAN,
         source="desk"):
    guest = guest.strip()
    if not guest:
        raise ValidationError("Guest name is required")
    check_stay(hotel, settings, room_type=room_type, arrival=arrival, departure=departure, adults=adults,
               rate_plan=rate_plan)
    _check_free(hotel, room_type, arrival, departure)
    reservation = Reservation(
        id=_next_id(hotel),
        guest=guest,
        room_type=room_type,
        arrival=arrival,
        departure=departure,
        adults=adults,
        rate_plan=rate_plan,
        rates=pricing.nightly_rates(hotel, settings, room_type, rate_plan, arrival, departure),
        source=source,
    )
    hotel.reservations[reservation.id] = reservation
    return reservation


def change_dates(hotel, settings, reservation_id, arrival, departure):
    """Move a booked stay; its nights are priced again at today's rates."""
    reservation = hotel.reservation(reservation_id)
    if reservation.status != BOOKED:
        raise InvalidState(f"Reservation {reservation.id} is {reservation.status}; only booked stays can move")
    check_stay(hotel, settings, room_type=reservation.room_type, arrival=arrival, departure=departure,
               adults=reservation.adults, rate_plan=reservation.rate_plan)
    _check_free(hotel, reservation.room_type, arrival, departure, excluding=reservation.id)
    reservation.arrival = arrival
    reservation.departure = departure
    reservation.rates = pricing.nightly_rates(hotel, settings, reservation.room_type, reservation.rate_plan,
                                              arrival, departure)
    return reservation


def cancel(hotel, reservation_id):
    reservation = hotel.reservation(reservation_id)
    if reservation.status != BOOKED:
        raise InvalidState(f"Reservation {reservation.id} is {reservation.status} and cannot be cancelled")
    reservation.status = CANCELLED
    reservation.cancelled_on = hotel.business_date
    return reservation


def reinstate(hotel, reservation_id):
    """Undo a no-show for a guest who turns up after all, if a room of the type is still free."""
    reservation = hotel.reservation(reservation_id)
    if reservation.status != NO_SHOW:
        raise InvalidState(f"Reservation {reservation.id} is {reservation.status}, not a no-show")
    if reservation.departure <= hotel.business_date:
        raise InvalidState(f"Reservation {reservation.id} ended on {reservation.departure.isoformat()}")
    # The missed nights are gone; the stay starts again on the business date.
    missed = (hotel.business_date - reservation.arrival).days
    reservation.rates = reservation.rates[missed:]
    reservation.arrival = hotel.business_date
    _check_free(hotel, reservation.room_type, reservation.arrival, reservation.departure)
    reservation.status = BOOKED
    return reservation


def arriving(hotel, day):
    return sorted((r for r in hotel.reservations.values() if r.status == BOOKED and r.arrival == day),
                  key=lambda r: r.guest)


def departing(hotel, day):
    return sorted((r for r in hotel.reservations.values() if r.status == IN_HOUSE and r.departure == day),
                  key=lambda r: r.room)


def staying(hotel):
    return sorted(hotel.reservations_with(IN_HOUSE), key=lambda r: r.room)
