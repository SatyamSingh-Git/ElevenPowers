"""The day schedule: who sees whom, where and when. Reception prints the export each morning."""
import csv
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path

TIME_FORMAT = "%H:%M"
COLUMNS = ("date", "start", "end", "practitioner", "room", "patient", "phone", "status")
STATUS_TEXT = {
    "booked": "Booked",
    "attended": "Attended",
    "no_show": "No-show",
    "cancelled": "Cancelled",
}


@dataclass(frozen=True)
class ScheduleRow:
    day: date
    start: time
    end: time
    practitioner: str
    room: str
    patient: str
    phone: str
    status: str

    @property
    def status_text(self):
        return STATUS_TEXT[self.status]


def schedule_rows(bookings, clinic, day):
    """The day's bookings, cancelled ones included, in the order they are given.

    Bookings come from the bookings file, which keeps them by day and start
    time, so the rows read from the first appointment of the day to the last.
    """
    return [
        ScheduleRow(
            day=booking.day,
            start=booking.start,
            end=booking.end,
            practitioner=clinic.practitioner_name(booking.practitioner),
            room=booking.room,
            patient=booking.patient,
            phone=booking.phone,
            status=booking.status,
        )
        for booking in bookings
        if booking.day == day
    ]


def default_export_name(day):
    return f"schedule-{day.isoformat()}.csv"


def export_day(bookings, clinic, day, path):
    """Write the day schedule as CSV; returns how many rows were written."""
    rows = schedule_rows(bookings, clinic, day)
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([
                row.day.isoformat(),
                row.start.strftime(TIME_FORMAT),
                row.end.strftime(TIME_FORMAT),
                row.practitioner,
                row.room,
                row.patient,
                row.phone,
                row.status_text,
            ])
    return len(rows)
