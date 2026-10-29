"""The patient directory, built from the bookings. Patients are known by phone number."""
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..model.booking import ATTENDED, NO_SHOW

DIRECTORY_COLUMNS = ("name", "phone", "bookings", "no_shows", "last_visit")


@dataclass(frozen=True)
class PatientRecord:
    phone: str
    name: str
    bookings: int
    no_shows: int
    last_visit: date | None


def directory(bookings):
    """One record per phone number, under the name used most recently, sorted by name."""
    grouped = {}
    for booking in sorted(bookings, key=lambda b: (b.starts_at, b.id)):
        grouped.setdefault(booking.phone, []).append(booking)
    records = []
    for phone, theirs in grouped.items():
        visits = [b.day for b in theirs if b.status == ATTENDED]
        records.append(PatientRecord(
            phone=phone,
            name=theirs[-1].patient,
            bookings=len(theirs),
            no_shows=sum(1 for b in theirs if b.status == NO_SHOW),
            last_visit=max(visits, default=None),
        ))
    return sorted(records, key=lambda record: (record.name.casefold(), record.phone))


def frequent_no_shows(records, at_least):
    """Patients who have missed `at_least` appointments, most missed first."""
    found = [record for record in records if record.no_shows >= at_least]
    return sorted(found, key=lambda record: (-record.no_shows, record.name.casefold()))


def write_directory(records, path):
    """The directory as CSV, for the practice manager's spreadsheet."""
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(DIRECTORY_COLUMNS)
        for record in records:
            last = record.last_visit.isoformat() if record.last_visit else ""
            writer.writerow([record.name, record.phone, record.bookings, record.no_shows, last])


def search(records, text):
    """Records whose name contains `text`, or whose phone number starts with it."""
    needle = text.strip().casefold()
    digits = needle.replace(" ", "")
    return [
        record for record in records
        if needle in record.name.casefold() or (digits.isdigit() and record.phone.startswith(digits))
    ]
