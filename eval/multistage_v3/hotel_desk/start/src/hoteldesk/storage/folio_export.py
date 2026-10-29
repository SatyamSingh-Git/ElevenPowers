"""Folio charges as CSV, one line per charge, for the accounts package."""
import csv
from pathlib import Path

from ..money import format_money

COLUMNS = ("reservation", "guest", "date", "code", "description", "amount")


def export_folios(hotel, path, day=None):
    """Write every charge (only those dated `day`, if given); returns how many were written."""
    written = 0
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for reservation_id in sorted(hotel.folios):
            guest = hotel.reservation(reservation_id).guest
            for charge in hotel.folios[reservation_id].charges:
                if day is not None and charge.day != day:
                    continue
                writer.writerow([reservation_id, guest, charge.day.isoformat(), charge.code,
                                 charge.description, format_money(charge.amount)])
                written += 1
    return written
