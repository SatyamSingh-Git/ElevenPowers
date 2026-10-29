"""The readings log, ``readings.csv``: every accepted reading, in arrival order.

Values are written in their kind's canonical unit with the catalog's number of
decimals. The log is only ever appended to.
"""
import csv
from pathlib import Path

from ..core.clock import format_timestamp
from ..core.units import format_value

LOG_COLUMNS = ["timestamp", "zone", "sensor", "kind", "value", "unit"]


class ReadingsLog:
    def __init__(self, path):
        self.path = Path(path)

    def write_many(self, readings):
        """Append readings, starting the file with its column names; return how many."""
        fresh = not self.path.exists() or self.path.stat().st_size == 0
        count = 0
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            if fresh:
                writer.writerow(LOG_COLUMNS)
            for reading in readings:
                writer.writerow(_log_row(reading))
                count += 1
        return count

    def write(self, reading):
        self.write_many([reading])


def _log_row(reading):
    return [
        format_timestamp(reading.at),
        reading.zone,
        reading.sensor,
        reading.kind,
        format_value(reading.kind, reading.value),
        reading.unit,
    ]
