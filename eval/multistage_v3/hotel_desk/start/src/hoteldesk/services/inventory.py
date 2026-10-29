"""How many rooms are free, sold or out of order on a given night."""
from datetime import timedelta

from ..dates import nights
from ..model.reservations import CHECKED_OUT, HOLDING
from ..money import per

# A night counts as sold once a guest holds the room for it or has already stayed it.
SOLD = HOLDING + (CHECKED_OUT,)


def held(hotel, room_type, day, excluding=None):
    return sum(
        1
        for reservation in hotel.reservations.values()
        if reservation.room_type == room_type
        and reservation.status in HOLDING
        and reservation.covers(day)
        and reservation.id != excluding
    )


def free(hotel, room_type, day, excluding=None):
    sellable = sum(1 for room in hotel.rooms_of_type(room_type) if room.sellable)
    return sellable - held(hotel, room_type, day, excluding)


def first_full_night(hotel, room_type, arrival, departure, excluding=None):
    """The first night of the stay with no room of that type left, if there is one."""
    for night in nights(arrival, departure):
        if free(hotel, room_type, night, excluding) <= 0:
            return night
    return None


def availability(hotel, start, days):
    """Free rooms of each type for each of `days` nights from `start`."""
    dates = nights(start, start + timedelta(days=days))
    return {code: [free(hotel, code, day) for day in dates] for code in sorted(hotel.room_types)}


def day_statistics(hotel, day):
    """Rooms, rooms sold and room revenue for one night, with occupancy, ADR and RevPAR."""
    rooms = len(hotel.rooms)
    out_of_order = sum(1 for room in hotel.rooms.values() if not room.sellable)
    available = rooms - out_of_order
    staying = [r for r in hotel.reservations.values() if r.status in SOLD and r.covers(day)]
    revenue = sum(reservation.rate_for(day) for reservation in staying)
    return {
        "date": day.isoformat(),
        "rooms": rooms,
        "out_of_order": out_of_order,
        "available": available,
        "sold": len(staying),
        "occupancy": round(len(staying) / available, 4) if available else 0.0,
        "room_revenue": revenue,
        "adr": per(revenue, len(staying)),
        "revpar": per(revenue, available),
    }
