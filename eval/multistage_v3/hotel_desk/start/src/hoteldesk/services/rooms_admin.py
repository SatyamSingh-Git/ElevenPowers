"""Changes to the room inventory after setup: new rooms, retyped rooms, new base rates."""
from ..dates import nights
from ..errors import InvalidState, ValidationError
from ..model.reservations import HOLDING
from ..model.rooms import Room
from . import inventory


def add_room(hotel, number, type_code, floor=None):
    number = str(number)
    if not number.isdigit():
        raise ValidationError(f"Room numbers are digits only: {number}")
    if number in hotel.rooms:
        raise ValidationError(f"Duplicate room: {number}")
    hotel.room_type(type_code)
    room = Room(number, type_code, int(number[:-2] or 0) if floor is None else floor)
    hotel.rooms[number] = room
    return room


def _booked_nights(hotel, type_code):
    return sorted({
        night
        for reservation in hotel.reservations.values()
        if reservation.room_type == type_code and reservation.status in HOLDING
        for night in nights(reservation.arrival, reservation.departure)
    })


def change_room_type(hotel, number, type_code):
    """Retype a vacant room, as long as every booking of its old type still has a room."""
    room = hotel.room(number)
    hotel.room_type(type_code)
    if room.occupied:
        raise InvalidState(f"Room {room.number} is occupied")
    old_type = room.type_code
    room.type_code = type_code
    for night in _booked_nights(hotel, old_type):
        if inventory.free(hotel, old_type, night) < 0:
            room.type_code = old_type
            raise InvalidState(f"Room {room.number} is needed for {old_type} bookings on {night.isoformat()}")
    return room


def set_base_rate(hotel, type_code, cents):
    """A new base rate for bookings taken from now on; existing reservations keep their rates."""
    if cents <= 0:
        raise ValidationError("Base rate must be positive")
    room_type = hotel.room_type(type_code)
    room_type.base_rate = cents
    return room_type
