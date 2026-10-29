"""The state file: everything the desk knows, saved between commands as JSON.

Dates are ISO strings and money is integer cents.
"""
from dataclasses import asdict
from datetime import date, datetime
import json
import os
from pathlib import Path

from ..errors import NotFound, ValidationError
from ..model.desk_log import LostItem, WakeUpCall
from ..model.folios import Charge, Folio, Payment
from ..model.guests import Guest
from ..model.hotel import Hotel
from ..model.rates import RatePlan
from ..model.reservations import Reservation
from ..model.rooms import Room, RoomType

FORMAT_VERSION = 1


def _iso(value):
    return value.isoformat() if value is not None else None


def _reservation_to_dict(reservation):
    data = asdict(reservation)
    for key in ("arrival", "departure", "checked_in_at", "checked_out_at", "cancelled_on"):
        data[key] = _iso(data[key])
    return data


def _reservation_from_dict(data):
    data = dict(data)
    for key in ("arrival", "departure", "cancelled_on"):
        data[key] = date.fromisoformat(data[key]) if data[key] else None
    for key in ("checked_in_at", "checked_out_at"):
        data[key] = datetime.fromisoformat(data[key]) if data[key] else None
    return Reservation(**data)


def _folio_to_dict(folio):
    return {
        "reservation_id": folio.reservation_id,
        "charges": [{**asdict(charge), "day": charge.day.isoformat()} for charge in folio.charges],
        "payments": [{**asdict(payment), "day": payment.day.isoformat()} for payment in folio.payments],
    }


def _folio_from_dict(data):
    return Folio(
        data["reservation_id"],
        [Charge(**{**item, "day": date.fromisoformat(item["day"])}) for item in data["charges"]],
        [Payment(**{**item, "day": date.fromisoformat(item["day"])}) for item in data["payments"]],
    )


def hotel_to_dict(hotel):
    return {
        "format": FORMAT_VERSION,
        "name": hotel.name,
        "business_date": hotel.business_date.isoformat(),
        "room_types": [asdict(room_type) for room_type in hotel.room_types.values()],
        "rooms": [asdict(room) for room in hotel.rooms.values()],
        "rate_plans": [asdict(plan) for plan in hotel.rate_plans.values()],
        "reservations": [_reservation_to_dict(r) for r in hotel.reservations.values()],
        "folios": [_folio_to_dict(folio) for folio in hotel.folios.values()],
        "guests": [asdict(guest) for guest in hotel.guests.values()],
        "wake_up_calls": [{**asdict(call), "at": call.at.isoformat()} for call in hotel.wake_up_calls],
        "lost_items": [{**asdict(item), "found_on": item.found_on.isoformat()} for item in hotel.lost_items],
    }


def hotel_from_dict(data):
    if data.get("format") != FORMAT_VERSION:
        raise ValidationError(f"Unsupported state format: {data.get('format')}")
    reservations = [_reservation_from_dict(item) for item in data["reservations"]]
    folios = [_folio_from_dict(item) for item in data["folios"]]
    return Hotel(
        name=data["name"],
        business_date=date.fromisoformat(data["business_date"]),
        room_types={item["code"]: RoomType(**item) for item in data["room_types"]},
        rooms={item["number"]: Room(**item) for item in data["rooms"]},
        rate_plans={item["code"]: RatePlan(**item) for item in data["rate_plans"]},
        reservations={reservation.id: reservation for reservation in reservations},
        folios={folio.reservation_id: folio for folio in folios},
        guests={item["name"]: Guest(**item) for item in data["guests"]},
        wake_up_calls=[WakeUpCall(**{**item, "at": datetime.fromisoformat(item["at"])})
                       for item in data["wake_up_calls"]],
        lost_items=[LostItem(**{**item, "found_on": date.fromisoformat(item["found_on"])})
                    for item in data["lost_items"]],
    )


def save_hotel(hotel, path):
    path = Path(path)
    # Write beside the real file and swap, so a crash never leaves half a state file.
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(hotel_to_dict(hotel), indent=2) + "\n", encoding="utf-8")
    os.replace(partial, path)


def load_hotel(path):
    path = Path(path)
    if not path.is_file():
        raise NotFound(f"No state file at {path}; run `hoteldesk init` first")
    return hotel_from_dict(json.loads(path.read_text(encoding="utf-8")))
