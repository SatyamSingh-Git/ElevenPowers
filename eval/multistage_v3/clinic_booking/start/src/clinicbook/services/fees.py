"""No-show fees, and the charges file the card terminal takes them from."""
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..model.booking import NO_SHOW

DEFAULT_NAME = "charges.csv"
NO_SHOW_REASON = "no-show"
COLUMNS = ("booking", "patient", "phone", "day", "reason", "amount")


@dataclass(frozen=True)
class Charge:
    booking: str
    patient: str
    phone: str
    day: date
    reason: str
    amount: Decimal


def charges(bookings, settings):
    """What patients owe: one charge per no-show, by day and booking reference."""
    owed = [
        Charge(booking.id, booking.patient, booking.phone, booking.day, NO_SHOW_REASON, settings.no_show_fee)
        for booking in bookings
        if booking.status == NO_SHOW
    ]
    return sorted(owed, key=lambda charge: (charge.day, charge.booking))


def total(owed):
    return sum((charge.amount for charge in owed), Decimal("0.00"))


def by_patient(owed):
    """Charges grouped by phone number, each group in the order given."""
    grouped = {}
    for charge in owed:
        grouped.setdefault(charge.phone, []).append(charge)
    return grouped


def write_charges(owed, path=DEFAULT_NAME):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for charge in owed:
            writer.writerow([
                charge.booking,
                charge.patient,
                charge.phone,
                charge.day.isoformat(),
                charge.reason,
                f"{charge.amount:.2f}",
            ])
