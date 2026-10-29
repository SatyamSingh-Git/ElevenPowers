"""Text-message reminders, queued in an outbox file the SMS gateway collects."""
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..errors import StorageError
from ..model.booking import BOOKED

DEFAULT_OUTBOX = "outbox.csv"
OUTBOX_COLUMNS = ("booking", "phone", "send_at", "text")
TEXT = ("{patient}, a reminder of your appointment with {practitioner} "
        "at {time} on {day}. Reply C to cancel.")


@dataclass(frozen=True)
class Reminder:
    booking: str
    phone: str
    send_at: datetime
    text: str


def reminder_text(booking, clinic):
    first_name = booking.patient.split()[0]
    return TEXT.format(
        patient=first_name,
        practitioner=clinic.practitioner_name(booking.practitioner),
        time=f"{booking.start:%H:%M}",
        day=f"{booking.day:%A %d %B}",
    )


def due_reminders(bookings, clinic, now, already_sent=frozenset()):
    """Reminders for bookings starting within the lead time, soonest first.

    A booking is reminded once: anything in `already_sent` is skipped.
    """
    lead = timedelta(hours=clinic.settings.reminder_lead_hours)
    due = []
    for booking in sorted(bookings, key=lambda b: (b.starts_at, b.id)):
        if booking.status != BOOKED or booking.id in already_sent:
            continue
        if now < booking.starts_at <= now + lead:
            due.append(Reminder(booking.id, booking.phone, now, reminder_text(booking, clinic)))
    return due


def read_sent(path=DEFAULT_OUTBOX):
    """References of bookings already queued in the outbox."""
    path = Path(path)
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != OUTBOX_COLUMNS:
            raise StorageError(f"{path}: expected columns {','.join(OUTBOX_COLUMNS)}")
        return {row["booking"] for row in reader}


def append_outbox(reminders, path=DEFAULT_OUTBOX):
    path = Path(path)
    fresh = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if fresh:
            writer.writerow(OUTBOX_COLUMNS)
        for reminder in reminders:
            writer.writerow([reminder.booking, reminder.phone,
                             reminder.send_at.isoformat(timespec="minutes"), reminder.text])
