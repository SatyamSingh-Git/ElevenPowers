from datetime import date, datetime, time
import json

import pytest

from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.storage.clinic_file import parse_clinic

MONDAY = date(2026, 3, 2)
SUNDAY = date(2026, 3, 1)

CLINIC = {
    "name": "Riverside Physio",
    "rooms": [
        {"id": "R1", "name": "Room 1"},
        {"id": "R2", "name": "Room 2"},
        {"id": "R3", "name": "Gym", "accessible": False},
    ],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
        {"id": "ben", "name": "Ben Okafor", "specialty": "osteopathy", "room": "R2",
         "days": ["mon", "wed", "fri"]},
        {"id": "cara", "name": "Cara Diaz", "specialty": "sports massage", "room": "R3",
         "days": ["tue", "thu", "sat"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00",
              "thu": "09:00-17:00", "fri": "09:00-17:00", "sat": "09:00-13:00", "sun": None},
    "closures": ["2026-03-20"],
}


def at(text):
    hours, minutes = text.split(":")
    return time(int(hours), int(minutes))


@pytest.fixture
def clinic():
    return parse_clinic(CLINIC)


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 2, 27, 8, 0))


@pytest.fixture
def desk(clinic, clock):
    return Desk(clinic, [], clock)


@pytest.fixture
def clinic_file(tmp_path):
    path = tmp_path / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    return path
