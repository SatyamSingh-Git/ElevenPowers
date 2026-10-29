"""Room types, rooms and their housekeeping status."""
from dataclasses import dataclass

CLEAN = "clean"
DIRTY = "dirty"
INSPECTED = "inspected"
OUT_OF_ORDER = "out_of_order"

HOUSEKEEPING_STATUSES = (CLEAN, DIRTY, INSPECTED, OUT_OF_ORDER)
# A guest may be roomed in either; inspected means a supervisor has signed the room off.
READY_STATUSES = (CLEAN, INSPECTED)


@dataclass
class RoomType:
    code: str
    name: str
    max_adults: int
    base_rate: int


@dataclass
class Room:
    number: str
    type_code: str
    floor: int
    status: str = CLEAN
    occupied: bool = False

    @property
    def ready(self):
        return self.status in READY_STATUSES and not self.occupied

    @property
    def sellable(self):
        return self.status != OUT_OF_ORDER
