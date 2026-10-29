"""The `clinic` command line."""
import argparse
import sys

from ..errors import ClinicError
from ..services.fees import DEFAULT_NAME as CHARGES_FILE
from ..services.reminders import DEFAULT_OUTBOX
from ..storage.bookings_file import DEFAULT_NAME as BOOKINGS_FILE
from ..storage.clinic_file import DEFAULT_NAME as CLINIC_FILE
from ..storage.waitlist_file import DEFAULT_NAME as WAITLIST_FILE
from . import commands
from .parsing import positive

DEFAULT_SLOT_DAYS = 7


def _days(text):
    try:
        return positive(text)
    except ClinicError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def build_parser():
    parser = argparse.ArgumentParser(prog="clinic", description="Appointment booking for a small clinic.")
    parser.add_argument("--clinic", default=CLINIC_FILE, help=f"clinic file (default: {CLINIC_FILE})")
    parser.add_argument("--bookings", default=BOOKINGS_FILE, help=f"bookings file (default: {BOOKINGS_FILE})")
    parser.add_argument("--now", help="the current time as YYYY-MM-DDTHH:MM (default: the system clock)")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    def command(name, handler, summary):
        found = sub.add_parser(name, help=summary, description=summary)
        found.set_defaults(handler=handler)
        return found

    command("init", commands.init, "write a starter clinic file").set_defaults(needs_clinic=False)
    command("practitioners", commands.practitioners, "list the practitioners")
    command("rooms", commands.rooms, "list the rooms")
    command("settings", commands.settings, "show the clinic's settings")

    found = command("hours", commands.hours, "show opening hours and coming closures")
    found.add_argument("--from", dest="start", help="first day to look at (default: today)")
    found.add_argument("--days", type=_days, default=28, help="how many days to look ahead (default: 28)")

    found = command("slots", commands.slots, "list free slots")
    found.add_argument("--from", dest="start", help="first day to list (default: today)")
    found.add_argument("--days", type=_days, default=DEFAULT_SLOT_DAYS,
                       help=f"how many days to list (default: {DEFAULT_SLOT_DAYS})")
    found.add_argument("--practitioner", help="only this practitioner's slots")

    found = command("book", commands.book, "book an appointment")
    found.add_argument("practitioner")
    found.add_argument("day", help="YYYY-MM-DD, today, tomorrow or a weekday")
    found.add_argument("time", help="HH:MM")
    found.add_argument("--patient", required=True, help="the patient's full name")
    found.add_argument("--phone", required=True, help="the patient's phone number")
    found.add_argument("--weeks", type=_days, default=1, help="book the same time this many weeks running")

    for name, handler, summary in (
        ("cancel", commands.cancel, "cancel a booking"),
        ("attend", commands.attend, "record that the patient came"),
        ("no-show", commands.no_show, "record that the patient did not come"),
    ):
        command(name, handler, summary).add_argument("booking", help="booking reference, e.g. B0042")

    command("list", commands.list_day, "list one day's bookings").add_argument("day")

    found = command("schedule", commands.schedule, "export one day's schedule as CSV")
    found.add_argument("day")
    found.add_argument("--out", help="file to write (default: schedule-<day>.csv)")

    command("utilisation", commands.utilisation, "room use from an exported day schedule").add_argument("path")
    command("summary", commands.summary, "end-of-day summary").add_argument("day")

    found = command("fees", commands.fees, "list no-show charges")
    found.add_argument("--out", help=f"also write them to this charges file, e.g. {CHARGES_FILE}")

    found = command("statement", commands.statement, "one patient's charges, from a charges file")
    found.add_argument("phone")
    found.add_argument("--charges", default=CHARGES_FILE, help=f"charges file (default: {CHARGES_FILE})")

    found = command("reminders", commands.reminders, "queue reminders that are due")
    found.add_argument("--outbox", default=DEFAULT_OUTBOX, help=f"outbox file (default: {DEFAULT_OUTBOX})")
    found.add_argument("--dry-run", action="store_true", help="show the reminders without queueing them")

    command("week", commands.week, "a week at a glance").add_argument("day", nargs="?")
    command("month", commands.month, "a month at a glance").add_argument("day", nargs="?")

    found = command("archive", commands.archive, "move old bookings into yearly archive files")
    found.add_argument("before", help="archive bookings before this day")

    found = command("attendance", commands.attendance, "how often patients came, per practitioner")
    found.add_argument("first")
    found.add_argument("last")

    found = command("calendar", commands.calendar, "a practitioner's appointments as an .ics file")
    found.add_argument("practitioner")
    found.add_argument("first")
    found.add_argument("last")
    found.add_argument("--out", required=True, help="file to write")

    found = command("patients", commands.patients, "find patients by name or phone")
    found.add_argument("search", nargs="?")
    found.add_argument("--no-shows", type=_days, help="only patients with at least this many no-shows")
    found.add_argument("--out", help="write the list to this CSV file instead")

    found = command("next", commands.next_free, "the earliest free slot")
    found.add_argument("--from", dest="start", help="first day to look at (default: today)")
    found.add_argument("--practitioner", help="only this practitioner")

    command("close", commands.close, "add a one-off closure to the clinic file").add_argument("day")

    found = command("stranded", commands.stranded, "bookings on days the clinic is now shut")
    found.add_argument("--days", type=_days, default=60, help="how many days to look ahead (default: 60)")

    found = command("import", commands.import_partner, "book the rows of the partner's CSV file")
    found.add_argument("path")

    found = command("wait", commands.wait_add, "put a patient on the waiting list")
    found.add_argument("practitioner", help="practitioner id, or any")
    found.add_argument("earliest")
    found.add_argument("latest")
    found.add_argument("--patient", required=True)
    found.add_argument("--phone", required=True)
    found.add_argument("--waitlist", default=WAITLIST_FILE, help=f"waiting-list file (default: {WAITLIST_FILE})")

    for name, handler, summary in (
        ("waiting", commands.wait_list, "show the waiting list"),
        ("offers", commands.wait_offers, "free slots to offer waiting patients"),
    ):
        command(name, handler, summary).add_argument("--waitlist", default=WAITLIST_FILE)

    command("check", commands.check, "look for problems in the bookings file")
    command("history", commands.history, "what has happened to a booking").add_argument("booking")
    command("show", commands.show_booking, "everything about one booking").add_argument("booking")
    command("backups", commands.list_backups, "list backups of the bookings file")
    command("restore", commands.restore_backup, "put a backup of the bookings file back").add_argument(
        "number", type=_days, help="backup number, as the backups command lists them")

    found = command("sheet", commands.sheet, "one practitioner's day on a sheet")
    found.add_argument("practitioner")
    found.add_argument("day")

    found = command("sheets", commands.sheets, "every working practitioner's sheet, one file each")
    found.add_argument("day")
    found.add_argument("--folder", default="sheets", help="where to write them (default: sheets)")

    found = command("handover", commands.handover, "the evening note for tomorrow's desk")
    found.add_argument("--outbox", default=DEFAULT_OUTBOX, help=f"outbox file (default: {DEFAULT_OUTBOX})")

    found = command("unwait", commands.wait_remove, "take a patient off the waiting list")
    found.add_argument("phone")
    found.add_argument("--waitlist", default=WAITLIST_FILE)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if getattr(args, "needs_clinic", True):
            args.handler(args, commands.Context.from_args(args))
        else:
            args.handler(args)
    except ClinicError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
