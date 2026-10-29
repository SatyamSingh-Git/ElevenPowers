"""The clinic file: a JSON description of rooms, practitioners, hours and settings.

    {
      "name": "Riverside Physio",
      "rooms": [{"id": "R1", "name": "Room 1"}],
      "practitioners": [{"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy",
                         "room": "R1", "days": ["mon", "tue"]}],
      "hours": {"mon": "09:00-17:00", "sun": null},
      "closures": ["2026-08-24"],
      "settings": {"slot_minutes": 20}
    }
"""
from datetime import date
import json
from pathlib import Path

from ..config import settings_from_dict
from ..errors import ConfigError
from ..model.clinic import Clinic
from ..model.hours import WEEKDAYS, OpeningHours
from ..model.people import Practitioner, Room

DEFAULT_NAME = "clinic.json"


def _required(entry, key, what):
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{what} needs a {key}")
    return value.strip()


def _rooms(raw):
    if not isinstance(raw, list) or not raw:
        raise ConfigError("the clinic needs at least one room")
    rooms = []
    for entry in raw:
        room_id = _required(entry, "id", "every room")
        if any(room.id == room_id for room in rooms):
            raise ConfigError(f"room {room_id} is listed twice")
        accessible = entry.get("accessible", True)
        if not isinstance(accessible, bool):
            raise ConfigError(f"room {room_id}: accessible must be true or false")
        rooms.append(Room(room_id, _required(entry, "name", f"room {room_id}"), accessible))
    return rooms


def _practitioners(raw, rooms):
    if not isinstance(raw, list) or not raw:
        raise ConfigError("the clinic needs at least one practitioner")
    room_ids = {room.id for room in rooms}
    practitioners = []
    for entry in raw:
        practitioner_id = _required(entry, "id", "every practitioner")
        if any(other.id == practitioner_id for other in practitioners):
            raise ConfigError(f"practitioner {practitioner_id} is listed twice")
        what = f"practitioner {practitioner_id}"
        room = _required(entry, "room", what)
        if room not in room_ids:
            raise ConfigError(f"{what} works in unknown room {room}")
        days = entry.get("days", list(WEEKDAYS[:5]))
        if not isinstance(days, list) or not days:
            raise ConfigError(f"{what} needs a list of days")
        for day in days:
            if day not in WEEKDAYS:
                raise ConfigError(f"{what} works on unknown day {day}")
        practitioners.append(Practitioner(
            id=practitioner_id,
            name=_required(entry, "name", what),
            specialty=entry.get("specialty", ""),
            room=room,
            days=tuple(day for day in WEEKDAYS if day in days),
        ))
    _check_shared_rooms(practitioners)
    return practitioners


def _check_shared_rooms(practitioners):
    """Two practitioners may share a room, but not on the same weekday."""
    seen = {}
    for practitioner in practitioners:
        for day in practitioner.days:
            other = seen.setdefault((practitioner.room, day), practitioner)
            if other is not practitioner:
                raise ConfigError(
                    f"{other.id} and {practitioner.id} both use room {practitioner.room} on {day}")


def _hours(raw, closures):
    if not isinstance(raw, dict):
        raise ConfigError("hours must map weekdays to opening times")
    if not isinstance(closures, list):
        raise ConfigError("closures must be a list of dates")
    try:
        days = [date.fromisoformat(day) for day in closures]
        return OpeningHours.from_spec(raw, days)
    except ValueError as error:
        raise ConfigError(str(error)) from None


def parse_clinic(raw):
    """A Clinic from the decoded clinic file, or ConfigError naming the first problem."""
    if not isinstance(raw, dict):
        raise ConfigError("the clinic file must hold a JSON object")
    rooms = _rooms(raw.get("rooms"))
    return Clinic(
        name=raw.get("name", "Clinic"),
        rooms=rooms,
        practitioners=_practitioners(raw.get("practitioners"), rooms),
        hours=_hours(raw.get("hours"), raw.get("closures", [])),
        settings=settings_from_dict(raw.get("settings", {})),
    )


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"no clinic file at {path}") from None
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path} is not valid JSON: {error.msg} at line {error.lineno}") from None


def load_clinic(path=DEFAULT_NAME):
    return parse_clinic(_read(Path(path)))


def add_closure(path, day):
    """Add `day` to the clinic file's closures, keeping the rest of the file as it was.

    Returns False when the day was already listed.
    """
    path = Path(path)
    raw = _read(path)
    parse_clinic(raw)
    closures = raw.setdefault("closures", [])
    if day.isoformat() in closures:
        return False
    closures.append(day.isoformat())
    closures.sort()
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True
