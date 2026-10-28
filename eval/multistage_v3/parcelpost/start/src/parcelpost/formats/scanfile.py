"""The carrier's scan file: CSV with a header row, one scan per line."""
import csv
from dataclasses import dataclass
from datetime import datetime
import io

from ..core.errors import ScanError

HEADER = ["tracking_number", "code", "date", "time", "depot"]


@dataclass(frozen=True)
class ScanRow:
    line: int
    tracking_number: str
    code: str
    at: datetime
    depot: str


def parse_scan_file(text):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or [cell.strip() for cell in rows[0]] != HEADER:
        raise ScanError("scan file must start with the header " + ",".join(HEADER))
    scans = []
    for line, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(HEADER):
            raise ScanError(f"line {line}: expected {len(HEADER)} fields, found {len(row)}")
        number, code, day, clock, depot = (cell.strip() for cell in row)
        try:
            at = datetime.strptime(f"{day} {clock}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ScanError(f"line {line}: invalid date or time {day} {clock}") from None
        scans.append(ScanRow(line, number.upper(), code.upper(), at, depot.upper()))
    return scans
