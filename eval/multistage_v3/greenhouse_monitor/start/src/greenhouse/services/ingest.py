"""Import of controller exports into the readings log.

A controller export is a CSV file with the columns
``time,zone,sensor,kind,value,unit`` (in any order, extra columns ignored).
Each row is checked, converted to its kind's canonical unit and calibrated.
Rows that fail are reported by line number; the rest are logged together.
"""
import csv
from dataclasses import dataclass, field
from pathlib import Path

from ..core.clock import parse_timestamp
from ..core.errors import GreenhouseError, ValidationError
from ..core.model import Reading
from ..core.units import canonical_unit, check_kind, check_range, round_for, to_canonical

CONTROLLER_COLUMNS = ("time", "zone", "sensor", "kind", "value", "unit")


@dataclass
class IngestResult:
    imported: int = 0
    rejected: int = 0
    problems: list[str] = field(default_factory=list)


def ingest_file(path, log, layout, calibration):
    path = Path(path)
    if not path.is_file():
        raise ValidationError(f"no such file: {path}")
    result = IngestResult()
    readings = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        if set(CONTROLLER_COLUMNS) - set(rows.fieldnames or ()):
            raise ValidationError(f"{path.name}: expected columns {','.join(CONTROLLER_COLUMNS)}")
        for line, row in enumerate(rows, start=2):
            try:
                reading = parse_row(row, layout, calibration)
                if (reading.sensor, reading.at) in seen:
                    raise ValidationError(f"duplicate reading for {reading.sensor}")
            except GreenhouseError as error:
                result.rejected += 1
                result.problems.append(f"line {line}: {error}")
            else:
                seen.add((reading.sensor, reading.at))
                readings.append(reading)
    result.imported = log.write_many(readings)
    return result


def parse_row(row, layout, calibration):
    """One controller row as a calibrated Reading."""
    at = parse_timestamp(row["time"] or "")
    zone = layout.zone((row["zone"] or "").strip()).id
    sensor = (row["sensor"] or "").strip()
    if not sensor:
        raise ValidationError("missing sensor")
    kind = check_kind(row["kind"] or "")
    raw = to_canonical(kind, _number(row["value"] or ""), row["unit"] or "")
    value = check_range(kind, raw + calibration.offset_for(sensor))
    return Reading(
        at=at,
        zone=zone,
        sensor=sensor,
        kind=kind,
        value=round_for(kind, value),
        unit=canonical_unit(kind),
        raw=round_for(kind, raw),
    )


def _number(text):
    try:
        return float(text)
    except ValueError:
        raise ValidationError(f"bad value: {text.strip()}") from None
