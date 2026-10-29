"""A starter clinic file for a new installation, to be edited before first use."""
import json
from pathlib import Path

from ..errors import ConfigError

STARTER = {
    "name": "My Clinic",
    "rooms": [
        {"id": "R1", "name": "Room 1"},
        {"id": "R2", "name": "Room 2", "accessible": False},
    ],
    "practitioners": [
        {"id": "first", "name": "First Practitioner", "specialty": "physiotherapy",
         "room": "R1", "days": ["mon", "tue", "wed", "thu", "fri"]},
        {"id": "second", "name": "Second Practitioner", "specialty": "osteopathy",
         "room": "R2", "days": ["mon", "wed", "fri"]},
    ],
    "hours": {
        "mon": "09:00-17:00",
        "tue": "09:00-17:00",
        "wed": "09:00-17:00",
        "thu": "09:00-19:00",
        "fri": "09:00-17:00",
        "sat": "09:00-13:00",
        "sun": None,
    },
    "closures": [],
    "settings": {},
}


def write_starter(path):
    """Write the starter file; never over an existing one."""
    path = Path(path)
    if path.exists():
        raise ConfigError(f"{path} already exists")
    path.write_text(json.dumps(STARTER, indent=2) + "\n", encoding="utf-8")
    return path
