"""Small things the desk keeps track of overnight: wake-up calls and lost property."""
from dataclasses import dataclass
from datetime import date, datetime

HELD = "held"
RETURNED = "returned"
DISPOSED = "disposed"


@dataclass
class WakeUpCall:
    room: str
    at: datetime
    done: bool = False


@dataclass
class LostItem:
    number: int
    found_on: date
    where: str
    description: str
    status: str = HELD
    returned_to: str = ""
