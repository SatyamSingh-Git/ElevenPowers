"""Bookings delivered by the channel manager as a CSV file.

Each line is booked on its own; a line that cannot be booked is reported with
its line number and the rest of the file still goes in.
"""
import csv
from dataclasses import dataclass, field
from pathlib import Path

from ..dates import parse_date
from ..errors import HotelError, ValidationError
from ..services import booking

COLUMNS = ("channel_ref", "guest", "room_type", "arrival", "departure", "adults", "rate_plan")


@dataclass
class ImportResult:
    booked: list = field(default_factory=list)
    rejected: list = field(default_factory=list)


def _adults(text):
    if not text:
        return 1
    if not text.isdigit():
        raise ValidationError(f"Not a number of adults: {text}")
    return int(text)


def import_bookings(hotel, settings, path):
    result = ImportResult()
    seen = {reservation.source for reservation in hotel.reservations.values()}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise ValidationError(f"Channel file is missing columns: {', '.join(missing)}")
        for line, row in enumerate(reader, start=2):
            source = f"channel:{row['channel_ref']}"
            if source in seen:
                result.rejected.append((line, f"Duplicate channel reference {row['channel_ref']}"))
                continue
            try:
                reservation = booking.book(
                    hotel,
                    settings,
                    guest=row["guest"],
                    room_type=row["room_type"],
                    arrival=parse_date(row["arrival"]),
                    departure=parse_date(row["departure"]),
                    adults=_adults(row["adults"]),
                    rate_plan=row["rate_plan"] or booking.DEFAULT_PLAN,
                    source=source,
                )
            except HotelError as error:
                result.rejected.append((line, str(error)))
                continue
            seen.add(source)
            result.booked.append(reservation.id)
    return result
