"""The valve schedule for the irrigation controller, built from the irrigation plan.

The pump feeds one valve at a time, so zones run back to back from the start
time in the order the plan lists them. Each line of ``valves.txt`` reads
``HH:MM VALVE ZONE MINUTES``, which is what the controller's import expects.
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path

from ..core.errors import ValidationError

LINE = "{start} {valve} {zone} {minutes}"


def planned_minutes(path):
    """(zone, minutes) for each zone the plan waters, in plan order."""
    path = Path(path)
    if not path.exists():
        raise ValidationError(f"no irrigation plan: {path.name}")
    planned = []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.reader(handle)
        next(rows, None)
        for zone, minutes, _reason in rows:
            if int(minutes) > 0:
                planned.append((zone, int(minutes)))
    return planned


def build_schedule(planned, layout, start):
    """Schedule lines for ``planned`` zones, the first starting at ``start`` (hour, minute)."""
    slot = datetime(2000, 1, 1, *start)
    lines = []
    for zone_id, minutes in planned:
        valve = layout.zone(zone_id).valve
        lines.append(LINE.format(start=slot.strftime("%H:%M"), valve=valve, zone=zone_id, minutes=minutes))
        slot += timedelta(minutes=minutes)
    if slot.day != 1:
        raise ValidationError("the schedule runs past midnight")
    return lines


def write_schedule(path, lines):
    Path(path).write_text("".join(line + "\n" for line in lines), encoding="utf-8")
