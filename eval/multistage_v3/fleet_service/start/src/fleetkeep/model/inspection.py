"""What drivers and the yard find on walk-round inspections: defects and tyre tread."""
from dataclasses import dataclass
from datetime import date

from ..errors import FleetError

SEVERITIES = ("minor", "out-of-service")
TYRE_POSITIONS = ("LF", "RF", "LR", "RR", "LRO", "LRI", "RRO", "RRI")
MAX_TREAD_32NDS = 32


@dataclass
class Defect:
    id: str
    vehicle_id: str
    reported: date
    description: str
    severity: str = "minor"
    order_id: str = ""
    fixed: date | None = None

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise FleetError("E162", severity=self.severity)

    @property
    def is_open(self):
        return self.fixed is None

    @property
    def grounds_vehicle(self):
        return self.is_open and self.severity == "out-of-service"


@dataclass(frozen=True)
class TreadReading:
    """Tread depth at one wheel position, in 32nds of an inch."""

    vehicle_id: str
    day: date
    position: str
    depth: int

    def __post_init__(self):
        if self.position not in TYRE_POSITIONS:
            raise FleetError("E171", position=self.position, positions=",".join(TYRE_POSITIONS))
        if not 0 <= self.depth <= MAX_TREAD_32NDS:
            raise FleetError("E172", depth=self.depth)
