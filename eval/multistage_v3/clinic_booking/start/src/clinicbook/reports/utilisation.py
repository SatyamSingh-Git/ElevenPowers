"""Room utilisation for one day, worked out from an exported day schedule.

Reception exports each day with the `schedule` command. Reading that CSV back,
rather than the bookings file, means the figures match the sheet that was
printed, and schedules exported in the past can be measured too.
"""
import csv
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path

from ..errors import StorageError
from ..model.times import minutes_between
from .textfmt import percent, table

# Status labels for which the room was set aside, whether or not the patient came.
OCCUPYING = {"Booked", "Attended", "No-show"}


@dataclass(frozen=True)
class ExportedRow:
    day: date
    start: time
    end: time
    room: str
    status: str


@dataclass(frozen=True)
class RoomLoad:
    room: str
    name: str
    booked_minutes: int
    open_minutes: int

    @property
    def percent(self):
        if not self.open_minutes:
            return 0.0
        return 100 * self.booked_minutes / self.open_minutes


def read_schedule(path):
    path = Path(path)
    if not path.exists():
        raise StorageError(f"no day schedule at {path}")
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(ExportedRow(
                    day=date.fromisoformat(row["date"]),
                    start=time.fromisoformat(row["start"]),
                    end=time.fromisoformat(row["end"]),
                    room=row["room"],
                    status=row["status"],
                ))
            except (KeyError, ValueError) as error:
                raise StorageError(f"{path}:{reader.line_num}: not a day schedule row ({error})") from None
    return rows


def room_utilisation(path, clinic):
    """How many minutes each room was booked for, against the clinic's opening minutes."""
    rows = read_schedule(path)
    if not rows:
        return []
    days = {row.day for row in rows}
    if len(days) > 1:
        raise StorageError(f"{path} covers more than one day")
    open_minutes = clinic.hours.open_minutes(days.pop())
    booked = {room.id: 0 for room in clinic.rooms}
    for row in rows:
        if row.status in OCCUPYING and row.room in booked:
            booked[row.room] += minutes_between(row.start, row.end)
    return [RoomLoad(room.id, room.name, booked[room.id], open_minutes) for room in clinic.rooms]


def render_utilisation(loads):
    if not loads:
        return ["Nothing booked"]
    rows = [[load.name, load.booked_minutes, load.open_minutes, percent(load.percent)] for load in loads]
    return table(["room", "booked min", "open min", "used"], rows)
