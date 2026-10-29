"""Check-in, check-out and room moves."""
from ..errors import BalanceDue, InvalidState, RoomNotReady, Unavailable, ValidationError
from ..model.charges import LATE_CHECKOUT
from ..model.folios import Folio
from ..model.reservations import BOOKED, CHECKED_OUT, IN_HOUSE
from ..model.rooms import DIRTY
from ..money import format_money
from . import billing, inventory, pricing
from .stay_rules import check_length


def _choose_room(hotel, reservation, room_number):
    if room_number is None:
        # The lowest-numbered ready room of the booked type.
        for room in hotel.rooms_of_type(reservation.room_type):
            if room.ready:
                return room
        raise Unavailable(f"No {reservation.room_type} room is ready")
    room = hotel.room(room_number)
    if room.type_code != reservation.room_type:
        raise ValidationError(f"Room {room.number} is a {room.type_code} room, not {reservation.room_type}")
    if room.occupied:
        raise RoomNotReady(f"Room {room.number} is occupied")
    if not room.ready:
        raise RoomNotReady(f"Room {room.number} is not available")
    return room


def check_in(hotel, clock, reservation_id, room_number=None):
    reservation = hotel.reservation(reservation_id)
    if reservation.status != BOOKED:
        raise InvalidState(f"Reservation {reservation.id} is {reservation.status}")
    if reservation.arrival != hotel.business_date:
        raise InvalidState(f"Reservation {reservation.id} arrives on {reservation.arrival.isoformat()}")
    room = _choose_room(hotel, reservation, room_number)
    room.occupied = True
    reservation.room = room.number
    reservation.status = IN_HOUSE
    reservation.checked_in_at = clock.now()
    hotel.folios.setdefault(reservation.id, Folio(reservation.id))
    return room


def _late(settings, clock, today):
    now = clock.now()
    return now.date() == today and now.time() > settings.check_out_time


def check_out(hotel, settings, clock, reservation_id):
    """Settle and release the room. The folio must be paid in full first."""
    reservation = hotel.reservation(reservation_id)
    if reservation.status != IN_HOUSE:
        raise InvalidState(f"Reservation {reservation.id} is not in house")
    today = hotel.business_date
    folio = hotel.folio(reservation.id)
    already_charged = any(charge.code == LATE_CHECKOUT for charge in folio.charges_on(today))
    if _late(settings, clock, today) and not already_charged:
        billing.post_charge(hotel, reservation.id, LATE_CHECKOUT, settings.late_checkout_fee)
    if folio.balance > 0:
        raise BalanceDue(f"Balance due: {format_money(folio.balance)}")
    if reservation.departure > today:
        # Leaving early gives up the nights not yet posted.
        reservation.rates = reservation.rates[:(today - reservation.arrival).days]
        reservation.departure = today
    room = hotel.room(reservation.room)
    room.occupied = False
    room.status = DIRTY
    reservation.status = CHECKED_OUT
    reservation.checked_out_at = clock.now()
    return folio


def extend_stay(hotel, settings, reservation_id, departure):
    """Keep an in-house guest longer; the added nights are priced at today's rates."""
    reservation = hotel.reservation(reservation_id)
    if reservation.status != IN_HOUSE:
        raise InvalidState(f"Reservation {reservation.id} is not in house")
    if departure <= reservation.departure:
        raise ValidationError(f"New departure must be after {reservation.departure.isoformat()}")
    check_length(settings, (departure - reservation.arrival).days)
    night = inventory.first_full_night(hotel, reservation.room_type, reservation.departure, departure)
    if night is not None:
        raise Unavailable(f"No {reservation.room_type} rooms available on {night.isoformat()}")
    reservation.rates += pricing.nightly_rates(hotel, settings, reservation.room_type, reservation.rate_plan,
                                               reservation.departure, departure)
    reservation.departure = departure
    return reservation


def move_room(hotel, reservation_id, room_number):
    reservation = hotel.reservation(reservation_id)
    if reservation.status != IN_HOUSE:
        raise InvalidState(f"Reservation {reservation.id} is not in house")
    new_room = _choose_room(hotel, reservation, room_number)
    old_room = hotel.room(reservation.room)
    old_room.occupied = False
    old_room.status = DIRTY
    new_room.occupied = True
    reservation.room = new_room.number
    return new_room
