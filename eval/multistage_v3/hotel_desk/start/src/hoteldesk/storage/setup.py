"""Build a hotel from its setup file: room types, rooms and rate plans."""
from dataclasses import asdict
import json
from pathlib import Path

from ..errors import ValidationError
from ..model.hotel import Hotel
from ..model.rates import RatePlan
from ..model.rooms import Room, RoomType
from ..money import format_money, parse_money


def _room_types(items):
    room_types = {}
    for item in items:
        room_type = RoomType(item["code"], item["name"], int(item["max_adults"]), parse_money(item["base_rate"]))
        if room_type.code in room_types:
            raise ValidationError(f"Duplicate room type: {room_type.code}")
        room_types[room_type.code] = room_type
    return room_types


def _rooms(items, room_types):
    rooms = {}
    for item in items:
        number = str(item["number"])
        if not number.isdigit():
            raise ValidationError(f"Room numbers are digits only: {number}")
        if number in rooms:
            raise ValidationError(f"Duplicate room: {number}")
        if item["type"] not in room_types:
            raise ValidationError(f"Room {number} has unknown type {item['type']}")
        # Room 214 is on floor 2 unless the setup says otherwise.
        floor = int(item.get("floor", number[:-2] or 0))
        rooms[number] = Room(number, item["type"], floor)
    return rooms


def _rate_plans(items):
    plans = {}
    for item in items:
        plan = RatePlan(item["code"], item["name"], int(item.get("discount_percent", 0)),
                        int(item.get("min_nights", 1)), bool(item.get("breakfast", False)))
        if not 0 <= plan.discount_percent < 100:
            raise ValidationError(f"Rate plan {plan.code} discount must be between 0 and 99")
        if plan.code in plans:
            raise ValidationError(f"Duplicate rate plan: {plan.code}")
        plans[plan.code] = plan
    return plans


def build_hotel(data, business_date):
    try:
        room_types = _room_types(data["room_types"])
        rooms = _rooms(data["rooms"], room_types)
        plans = _rate_plans(data["rate_plans"])
    except KeyError as missing:
        raise ValidationError(f"Setup is missing {missing}") from None
    return Hotel(data.get("name", "Hotel"), business_date, room_types, rooms, plans)


def load_setup(path, business_date):
    return build_hotel(json.loads(Path(path).read_text(encoding="utf-8")), business_date)


def export_setup(hotel, path):
    """Write the hotel's current rooms, room types and rate plans back out as a setup file."""
    data = {
        "name": hotel.name,
        "room_types": [
            {"code": t.code, "name": t.name, "max_adults": t.max_adults, "base_rate": format_money(t.base_rate)}
            for t in hotel.room_types.values()
        ],
        "rooms": [{"number": room.number, "type": room.type_code, "floor": room.floor}
                  for room in sorted(hotel.rooms.values(), key=lambda room: room.number)],
        "rate_plans": [asdict(plan) for plan in hotel.rate_plans.values()],
    }
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
