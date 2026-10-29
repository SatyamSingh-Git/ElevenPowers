"""Who arrives, who leaves and who is in house."""
from ..money import format_money
from ..services import booking, guests

ARRIVAL_COLUMNS = ("reservation", "guest", "vip", "type", "nights", "adults", "plan", "breakfast")
DEPARTURE_COLUMNS = ("reservation", "guest", "room", "balance")
IN_HOUSE_COLUMNS = ("room", "reservation", "guest", "departure", "balance")


def _balance(hotel, reservation):
    folio = hotel.folios.get(reservation.id)
    return format_money(folio.balance if folio else 0)


def arrival_rows(hotel, day):
    return [
        {
            "reservation": r.id,
            "guest": r.guest,
            "vip": "yes" if guests.is_vip(hotel, r.guest) else "",
            "type": r.room_type,
            "nights": r.nights,
            "adults": r.adults,
            "plan": r.rate_plan,
            "breakfast": "yes" if hotel.rate_plan(r.rate_plan).breakfast else "no",
        }
        for r in booking.arriving(hotel, day)
    ]


def departure_rows(hotel, day):
    return [
        {"reservation": r.id, "guest": r.guest, "room": r.room, "balance": _balance(hotel, r)}
        for r in booking.departing(hotel, day)
    ]


def in_house_rows(hotel, day):
    # In house is always as of now; the day is accepted so every report reads alike.
    return [
        {"room": r.room, "reservation": r.id, "guest": r.guest, "departure": r.departure.isoformat(),
         "balance": _balance(hotel, r)}
        for r in booking.staying(hotel)
    ]
