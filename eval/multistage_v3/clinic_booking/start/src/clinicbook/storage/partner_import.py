"""Bookings taken by the online booking partner, imported from the CSV it emails each night.

The partner's file looks like this, with UK dates and practitioners by name:

    Date,Time,Clinician,Client,Mobile
    02/03/2026,9:00,Amy Hart,Ann Lee,07700900123

Every row goes through the front desk like a phone booking, so the same rules
apply. Rows that break a rule are reported and skipped; the rest are booked.
"""
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..errors import ClinicError, StorageError
from ..model.times import parse_hhmm

PARTNER_COLUMNS = ("Date", "Time", "Clinician", "Client", "Mobile")


@dataclass
class ImportReport:
    booked: list = field(default_factory=list)
    skipped: list = field(default_factory=list)

    def lines(self):
        lines = [f"Booked {len(self.booked)}, skipped {len(self.skipped)}"]
        lines += [f"  line {number}: {reason}" for number, reason in self.skipped]
        return lines


def _practitioner_ids(clinic):
    return {practitioner.name.casefold(): practitioner.id for practitioner in clinic.practitioners}


def _when(row):
    day = datetime.strptime(row["Date"].strip(), "%d/%m/%Y").date()
    hours, _, minutes = row["Time"].strip().partition(":")
    return day, parse_hhmm(f"{hours.zfill(2)}:{minutes}")


def import_partner_file(path, desk):
    """Book every acceptable row of the partner's file through `desk`."""
    path = Path(path)
    if not path.exists():
        raise StorageError(f"no partner file at {path}")
    ids = _practitioner_ids(desk.clinic)
    report = ImportReport()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PARTNER_COLUMNS:
            raise StorageError(f"{path}: expected columns {','.join(PARTNER_COLUMNS)}")
        for row in reader:
            number = reader.line_num
            practitioner = ids.get(row["Clinician"].strip().casefold())
            if practitioner is None:
                report.skipped.append((number, f"unknown clinician {row['Clinician'].strip()}"))
                continue
            try:
                day, start = _when(row)
            except ValueError:
                report.skipped.append((number, f"unreadable date or time {row['Date']} {row['Time']}"))
                continue
            try:
                report.booked.append(desk.book(practitioner, day, start, row["Client"], row["Mobile"]))
            except ClinicError as error:
                report.skipped.append((number, str(error)))
    return report
