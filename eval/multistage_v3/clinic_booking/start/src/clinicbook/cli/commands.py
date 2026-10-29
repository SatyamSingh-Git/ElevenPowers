"""One function per command. Each takes the parsed arguments and a Context and prints its result."""
from datetime import timedelta
from pathlib import Path

from ..clock import FixedClock, SystemClock
from ..config import settings_to_dict
from ..reports.attendance import attendance as attendance_between, render_attendance
from ..reports.calendar import calendar_lines, write_calendar
from ..reports.day_schedule import default_export_name, export_day, schedule_rows
from ..reports.handover import handover_lines
from ..reports.month import render_month
from ..reports.practitioner_sheet import sheet_lines
from ..reports.statement import render_statement, statement_from_file
from ..reports.summary import day_summary, render_summary
from ..reports.textfmt import table
from ..reports.utilisation import render_utilisation, room_utilisation
from ..reports.week import render_week
from ..services import audit, waitlist
from ..model.booking import BOOKED
from ..services.availability import first_free, free_slots_from
from ..services.checks import problems
from ..services.closures import stranded as stranded_bookings
from ..services.desk import Desk
from ..services.fees import charges, total, write_charges
from ..services.patients import directory, frequent_no_shows, search, write_directory
from ..services.reminders import append_outbox, due_reminders, read_sent
from ..services.series import book_series
from ..services.waitlist import new_entry
from ..storage.archive import archive_before
from ..storage.backups import backups, restore, take_backup
from ..storage.bookings_file import load_bookings, save_bookings
from ..storage.clinic_file import add_closure, load_clinic
from ..storage.partner_import import import_partner_file
from ..storage.starter import write_starter
from ..storage.waitlist_file import load_waitlist, save_waitlist
from .parsing import UsageError, parse_day, parse_moment, parse_time


class Context:
    """What every command needs: the clinic, where its bookings live, and the time."""

    def __init__(self, clinic, bookings_path, clock):
        self.clinic = clinic
        self.bookings_path = bookings_path
        self.clock = clock
        self._bookings = None

    @classmethod
    def from_args(cls, args):
        clock = FixedClock(parse_moment(args.now)) if args.now else SystemClock()
        return cls(load_clinic(args.clinic), args.bookings, clock)

    @property
    def bookings(self):
        if self._bookings is None:
            self._bookings = load_bookings(self.bookings_path)
        return self._bookings

    @property
    def today(self):
        return self.clock.now().date()

    def desk(self):
        return Desk(self.clinic, self.bookings, self.clock)

    @property
    def audit_path(self):
        return Path(self.bookings_path).with_name(audit.DEFAULT_NAME)

    def save(self, action, changed):
        """Back up the bookings file, write the bookings, and log what changed."""
        now = self.clock.now()
        take_backup(self.bookings_path, now)
        save_bookings(self.bookings, self.bookings_path)
        audit.record(self.audit_path, now, action, changed)

    def day(self, text):
        return parse_day(text, self.today)


def show(lines):
    for line in lines:
        print(line)


def practitioners(args, context):
    rows = [[p.id, p.name, p.specialty, p.room, " ".join(p.days)] for p in context.clinic.practitioners]
    show(table(["id", "name", "specialty", "room", "days"], rows))


def rooms(args, context):
    rows = []
    for room in context.clinic.rooms:
        users = [f"{p.name} ({' '.join(p.days)})" for p in context.clinic.practitioners if p.room == room.id]
        rows.append([room.id, room.name, "yes" if room.accessible else "no", "; ".join(users) or "-"])
    show(table(["id", "name", "step-free", "used by"], rows))


def hours(args, context):
    opening = context.clinic.hours
    show(opening.describe())
    first = context.day(args.start) if args.start else context.today
    upcoming = []
    for offset in range(args.days):
        day = first + timedelta(days=offset)
        if day in opening.holidays or day in opening.closures:
            upcoming.append(f"{day:%a %d %b}: {opening.closed_reason(day)}")
    if upcoming:
        print("Closures:")
        show(f"  {line}" for line in upcoming)


def settings(args, context):
    for name, value in settings_to_dict(context.clinic.settings).items():
        print(f"{name} = {value}")


def slots(args, context):
    first = context.day(args.start) if args.start else context.today
    found = free_slots_from(context.clinic, context.bookings, first, args.days,
                            context.clock.now(), args.practitioner)
    if not found:
        print("No free slots")
        reopens = context.clinic.hours.next_open_day(first)
        if reopens is not None and reopens != first:
            print(f"The clinic next opens on {reopens:%A %d %B}")
        return
    current = None
    for slot in found:
        if slot.day != current:
            current = slot.day
            print(f"{slot.day:%A %d %B}")
        name = context.clinic.practitioner_name(slot.practitioner)
        print(f"  {slot.start:%H:%M}  {name} ({slot.room})")


def book(args, context):
    made = book_series(context.desk(), args.practitioner, context.day(args.day), parse_time(args.time),
                       args.weeks, args.patient, args.phone)
    context.save("booked", made)
    for booking in made:
        print(f"Booked {booking.id} for {booking.patient} at {booking.start:%H:%M} on {booking.day}")


def cancel(args, context):
    booking = context.desk().cancel(args.booking)
    context.save("cancelled", [booking])
    print(f"Cancelled {booking.id}")


def attend(args, context):
    booking = context.desk().mark_attended(args.booking)
    context.save("attended", [booking])
    print(f"Marked {booking.id} attended")


def no_show(args, context):
    booking = context.desk().mark_no_show(args.booking)
    context.save("no-show", [booking])
    print(f"Marked {booking.id} as no-show")


def list_day(args, context):
    day = context.day(args.day)
    rows = schedule_rows(context.bookings, context.clinic, day)
    if not rows:
        print(f"No bookings on {day}")
        return
    cells = [[f"{row.start:%H:%M}", row.practitioner, row.room, row.patient, row.status_text] for row in rows]
    show(table(["time", "practitioner", "room", "patient", "status"], cells))


def schedule(args, context):
    day = context.day(args.day)
    path = args.out or default_export_name(day)
    count = export_day(context.bookings, context.clinic, day, path)
    print(f"Wrote {count} appointments to {path}")


def utilisation(args, context):
    show(render_utilisation(room_utilisation(args.path, context.clinic)))


def summary(args, context):
    show(render_summary(day_summary(context.bookings, context.clinic, context.day(args.day)), context.clinic))


def fees(args, context):
    owed = charges(context.bookings, context.clinic.settings)
    money = context.clinic.settings.money
    rows = [[c.booking, c.day.isoformat(), c.patient, c.phone, c.reason, money(c.amount)] for c in owed]
    if rows:
        show(table(["booking", "day", "patient", "phone", "reason", "amount"], rows))
    print(f"Total: {money(total(owed))}")
    if args.out:
        write_charges(owed, args.out)
        print(f"Wrote {len(owed)} charges to {args.out}")


def statement(args, context):
    show(render_statement(statement_from_file(args.charges, args.phone), context.clinic.settings))


def reminders(args, context):
    due = due_reminders(context.bookings, context.clinic, context.clock.now(), read_sent(args.outbox))
    if args.dry_run:
        for reminder in due:
            print(f"{reminder.phone}: {reminder.text}")
        print(f"{len(due)} reminders due")
        return
    append_outbox(due, args.outbox)
    print(f"Queued {len(due)} reminders in {args.outbox}")


def week(args, context):
    any_day = context.day(args.day) if args.day else context.today
    show(render_week(context.bookings, context.clinic, any_day))


def attendance(args, context):
    first, last = context.day(args.first), context.day(args.last)
    show(render_attendance(attendance_between(context.bookings, context.clinic, first, last), first, last))


def calendar(args, context):
    lines = calendar_lines(context.bookings, context.clinic, args.practitioner,
                           context.day(args.first), context.day(args.last))
    write_calendar(lines, args.out)
    print(f"Wrote {lines.count('BEGIN:VEVENT')} appointments to {args.out}")


def patients(args, context):
    records = directory(context.bookings)
    if args.search:
        records = search(records, args.search)
    if args.no_shows:
        records = frequent_no_shows(records, args.no_shows)
    if args.out:
        write_directory(records, args.out)
        print(f"Wrote {len(records)} patients to {args.out}")
        return
    if not records:
        print("No patients found")
        return
    rows = [[r.name, r.phone, r.bookings, r.no_shows, r.last_visit or "-"] for r in records]
    show(table(["name", "phone", "bookings", "no-shows", "last visit"], rows))


def next_free(args, context):
    first = context.day(args.start) if args.start else context.today
    slot = first_free(context.clinic, context.bookings, first, context.clinic.settings.booking_horizon_days,
                      context.clock.now(), args.practitioner)
    if slot is None:
        print("No free slots")
        return
    name = context.clinic.practitioner_name(slot.practitioner)
    print(f"{slot.day:%A %d %B} {slot.start:%H:%M} with {name} ({slot.room})")


def close(args, context):
    day = context.day(args.day)
    if not add_closure(args.clinic, day):
        print(f"{day} is already a closure")
        return
    print(f"The clinic is closed on {day}")
    affected = [b for b in context.bookings if b.day == day and b.status == BOOKED]
    if affected:
        print(f"{len(affected)} bookings on that day need moving; see the stranded command")


def stranded(args, context):
    found = stranded_bookings(context.bookings, context.clinic, context.today,
                              context.today + timedelta(days=args.days))
    if not found:
        print("No bookings to move")
        return
    for booking, reason in found:
        print(f"{booking.id}  {booking.day} {booking.start:%H:%M}  {booking.patient} {booking.phone}: {reason}")


def import_partner(args, context):
    report = import_partner_file(args.path, context.desk())
    context.save("imported", report.booked)
    show(report.lines())


def wait_add(args, context):
    entries = load_waitlist(args.waitlist)
    entry = new_entry(context.clinic, args.patient, args.phone, args.practitioner,
                      context.day(args.earliest), context.day(args.latest), context.clock.now())
    waitlist.add(entries, entry)
    save_waitlist(entries, args.waitlist)
    print(f"{entry.patient} is waiting for {entry.practitioner} between {entry.earliest} and {entry.latest}")


def wait_list(args, context):
    entries = load_waitlist(args.waitlist)
    if not entries:
        print("Nobody is waiting")
        return
    rows = [[e.patient, e.phone, e.practitioner, e.earliest, e.latest, e.added.date()] for e in entries]
    show(table(["patient", "phone", "practitioner", "from", "until", "added"], rows))


def wait_offers(args, context):
    found = waitlist.offers(load_waitlist(args.waitlist), context.clinic, context.bookings, context.clock.now())
    if not found:
        print("No offers to make")
        return
    for offer in found:
        slot = offer.slot
        name = context.clinic.practitioner_name(slot.practitioner)
        print(f"{offer.entry.patient} ({offer.entry.phone}): {slot.day:%a %d %b} {slot.start:%H:%M} with {name}")


def wait_remove(args, context):
    entries = load_waitlist(args.waitlist)
    removed = waitlist.remove(entries, args.phone)
    save_waitlist(entries, args.waitlist)
    print(f"Removed {removed} waiting-list entries")


def check(args, context):
    found = problems(context.bookings, context.clinic)
    show(found or ["No problems found"])


def sheet(args, context):
    show(sheet_lines(context.bookings, context.clinic, args.practitioner, context.day(args.day)))


def show_booking(args, context):
    booking = context.desk().find(args.booking)
    who = context.clinic.practitioner(booking.practitioner)
    show([
        f"{booking.id}  {booking.status}",
        f"  patient       {booking.patient} ({booking.phone})",
        f"  when          {booking.day:%A %d %B %Y} {booking.start:%H:%M}-{booking.end:%H:%M}",
        f"  practitioner  {who.name}, {who.specialty}",
        f"  room          {context.clinic.room(booking.room).name}",
        f"  booked        {booking.created:%d %b %Y %H:%M}" if booking.created else "  booked        (not recorded)",
    ])


def list_backups(args, context):
    found = backups(context.bookings_path)
    if not found:
        print("No backups yet")
        return
    show(f"{number}  {copy.name}" for number, copy in enumerate(found, 1))


def restore_backup(args, context):
    found = backups(context.bookings_path)
    if not 1 <= args.number <= len(found):
        raise UsageError(f"no backup {args.number}; the backups command lists them")
    take_backup(context.bookings_path, context.clock.now())
    restore(context.bookings_path, found[args.number - 1])
    print(f"Restored {found[args.number - 1].name}")


def handover(args, context):
    show(handover_lines(context.bookings, context.clinic, context.today, read_sent(args.outbox)))


def sheets(args, context):
    day = context.day(args.day)
    folder = Path(args.folder)
    folder.mkdir(parents=True, exist_ok=True)
    for practitioner in context.clinic.working_on(day):
        target = folder / f"{practitioner.id}-{day.isoformat()}.txt"
        lines = sheet_lines(context.bookings, context.clinic, practitioner.id, day)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {target}")


def history(args, context):
    show(audit.history(context.audit_path, args.booking) or [f"Nothing logged for {args.booking}"])


def month(args, context):
    any_day = context.day(args.day) if args.day else context.today
    show(render_month(context.bookings, context.clinic, any_day.year, any_day.month))


def archive(args, context):
    cutoff = context.day(args.before)
    take_backup(context.bookings_path, context.clock.now())
    moved = archive_before(context.bookings_path, cutoff)
    print(f"Archived {moved} bookings from before {cutoff}")


def init(args):
    print(f"Wrote {write_starter(args.clinic)}; edit it before taking bookings")
