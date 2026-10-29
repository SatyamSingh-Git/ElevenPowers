"""The bookings file: one CSV row per booking, rewritten in full on every save."""
import csv
from datetime import date, datetime, time
import os
from pathlib import Path

from ..errors import StorageError
from ..model.booking import STATUSES, Booking

DEFAULT_NAME = "bookings.csv"
COLUMNS = ("id", "patient", "phone", "practitioner", "room", "day", "start", "minutes", "status", "created")


def _file_order(booking):
    return (booking.day, booking.start, booking.practitioner)


def _row(booking):
    created = booking.created.isoformat(timespec="minutes") if booking.created else ""
    return [
        booking.id,
        booking.patient,
        booking.phone,
        booking.practitioner,
        booking.room,
        booking.day.isoformat(),
        booking.start.isoformat(timespec="minutes"),
        str(booking.minutes),
        booking.status,
        created,
    ]


def _booking(row, where):
    if row["status"] not in STATUSES:
        raise StorageError(f"{where}: unknown status {row['status']}")
    try:
        return Booking(
            id=row["id"],
            patient=row["patient"],
            phone=row["phone"],
            practitioner=row["practitioner"],
            room=row["room"],
            day=date.fromisoformat(row["day"]),
            start=time.fromisoformat(row["start"]),
            minutes=int(row["minutes"]),
            status=row["status"],
            created=datetime.fromisoformat(row["created"]) if row["created"] else None,
        )
    except (TypeError, ValueError) as error:
        raise StorageError(f"{where}: {error}") from None


def load_bookings(path=DEFAULT_NAME):
    """Bookings in the order the file holds them. A missing file means no bookings yet."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise StorageError(f"{path}: expected columns {','.join(COLUMNS)}")
        return [_booking(row, f"{path}:{reader.line_num}") for row in reader]


def save_bookings(bookings, path=DEFAULT_NAME):
    """Write every booking, sorted by day and start time.

    The new file replaces the old one only once it is complete, so a crash
    part-way through leaves the previous bookings intact.
    """
    path = Path(path)
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for booking in sorted(bookings, key=_file_order):
            writer.writerow(_row(booking))
    os.replace(partial, path)
