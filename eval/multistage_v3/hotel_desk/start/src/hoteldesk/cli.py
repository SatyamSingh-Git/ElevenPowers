"""Command line for the front desk: `python -m hoteldesk <command>`.

Every command loads the state file, does one thing and saves it again.
"""
import argparse
from datetime import datetime, time
from pathlib import Path
import sys

from ._generated import TAX_TABLE_EDITION
from .clock import FixedClock
from .config import load_settings
from .dates import format_time, nights, parse_date, parse_timestamp
from .errors import HotelError, ValidationError
from .money import format_money, parse_money
from .reports import audit_report, cashier, folio_print, guest_history, housekeeping_board, rate_sheet, revenue
from .reports.registry import FORMATS, REPORTS, render_report
from .reports.tables import table
from .services import billing, booking, desk_log, guests, housekeeping, night_audit, pricing, rooms_admin, stays
from .storage import backups, channel_import, folio_export, guest_import, setup, state

DEFAULT_STATE = "hotel-state.json"
DEFAULT_SETTINGS = "hotel.json"
# Without --now, a command acts at this time on the business date.
DEFAULT_TIME = time(10, 0)


class Desk:
    """What every command works on: the hotel, its settings and a clock."""

    def __init__(self, args):
        self.state_path = Path(args.state)
        self.settings = load_settings(args.settings)
        self.hotel = state.load_hotel(self.state_path)
        now = parse_timestamp(args.now) if args.now else datetime.combine(self.hotel.business_date, DEFAULT_TIME)
        self.clock = FixedClock(now)

    @property
    def journal_path(self):
        return self.state_path.parent / self.settings.journal_file

    def save(self):
        state.save_hotel(self.hotel, self.state_path)


def cmd_init(args):
    path = Path(args.state)
    if path.exists():
        raise ValidationError(f"State file {path} already exists")
    hotel = setup.load_setup(args.setup, parse_date(args.business_date))
    state.save_hotel(hotel, path)
    print(f"Set up {hotel.name}: {len(hotel.rooms)} rooms, business date {hotel.business_date.isoformat()}")


def cmd_quote(args):
    desk = Desk(args)
    arrival, departure = parse_date(args.arrival), parse_date(args.departure)
    offer = pricing.quote(desk.hotel, desk.settings, args.type, args.plan, arrival, departure, args.adults)
    for night, rate in zip(nights(arrival, departure), offer.rates):
        print(f"{night.isoformat()}  {format_money(rate)}")
    print(f"room {format_money(offer.room_total)}  tax {format_money(offer.tax)}  total {format_money(offer.total)}")


def cmd_book(args):
    desk = Desk(args)
    reservation = booking.book(desk.hotel, desk.settings, guest=args.guest, room_type=args.type,
                               arrival=parse_date(args.arrival), departure=parse_date(args.departure),
                               adults=args.adults, rate_plan=args.plan)
    desk.save()
    print(f"Booked {reservation.id}: {reservation.guest}, {reservation.room_type}, "
          f"{reservation.arrival.isoformat()} to {reservation.departure.isoformat()} "
          f"({reservation.nights} nights), {format_money(reservation.room_total)}")


def cmd_show(args):
    desk = Desk(args)
    r = desk.hotel.reservation(args.reservation)
    print(f"{r.id}  {r.guest}  {r.status}")
    print(f"{r.room_type} room {r.room or '-'}, {r.adults} adults, plan {r.rate_plan}, from {r.source}")
    print(f"{r.arrival.isoformat()} to {r.departure.isoformat()} ({r.nights} nights)")
    for night, rate in zip(nights(r.arrival, r.departure), r.rates):
        print(f"  {night.isoformat()}  {format_money(rate)}")
    folio = desk.hotel.folios.get(r.id)
    if folio is not None:
        print(f"balance {format_money(folio.balance)}")


def cmd_extend(args):
    desk = Desk(args)
    reservation = stays.extend_stay(desk.hotel, desk.settings, args.reservation, parse_date(args.departure))
    desk.save()
    print(f"{reservation.id} now leaves {reservation.departure.isoformat()}")


def cmd_settings(args):
    settings = load_settings(args.settings)
    for name, value in vars(settings).items():
        if name == "late_checkout_fee":
            value = format_money(value)
        elif isinstance(value, time):
            value = format_time(value)
        print(f"{name}: {value}")
    print(f"tax table: {TAX_TABLE_EDITION}")


def cmd_move_dates(args):
    desk = Desk(args)
    reservation = booking.change_dates(desk.hotel, desk.settings, args.reservation, parse_date(args.arrival),
                                       parse_date(args.departure))
    desk.save()
    print(f"{reservation.id} now {reservation.arrival.isoformat()} to {reservation.departure.isoformat()}, "
          f"{format_money(reservation.room_total)}")


def cmd_cancel(args):
    desk = Desk(args)
    reservation = booking.cancel(desk.hotel, args.reservation)
    desk.save()
    print(f"Cancelled {reservation.id}")


def cmd_reinstate(args):
    desk = Desk(args)
    reservation = booking.reinstate(desk.hotel, args.reservation)
    desk.save()
    print(f"{reservation.id} reinstated from {reservation.arrival.isoformat()}")


def cmd_checkin(args):
    desk = Desk(args)
    room = stays.check_in(desk.hotel, desk.clock, args.reservation, args.room)
    desk.save()
    print(f"{args.reservation} checked in to room {room.number}")


def cmd_checkout(args):
    desk = Desk(args)
    try:
        stays.check_out(desk.hotel, desk.settings, desk.clock, args.reservation)
    finally:
        # A late check-out fee stays posted even when the balance stops the check-out.
        desk.save()
    print(f"{args.reservation} checked out")


def cmd_move_room(args):
    desk = Desk(args)
    room = stays.move_room(desk.hotel, args.reservation, args.room)
    desk.save()
    print(f"{args.reservation} moved to room {room.number}")


def cmd_post(args):
    desk = Desk(args)
    posted = billing.post_charge(desk.hotel, args.reservation, args.code, parse_money(args.amount),
                                 args.description)
    desk.save()
    for charge in posted:
        print(f"Posted {charge.code} {format_money(charge.amount)} to {args.reservation}")


def cmd_transfer(args):
    desk = Desk(args)
    charge = billing.transfer_charge(desk.hotel, args.reservation, args.line - 1, args.to)
    desk.save()
    print(f"Moved {charge.description} {format_money(charge.amount)} to {args.to}")


def cmd_pay(args):
    desk = Desk(args)
    payment = billing.post_payment(desk.hotel, args.reservation, parse_money(args.amount), args.method)
    desk.save()
    balance = desk.hotel.folio(args.reservation).balance
    print(f"Paid {format_money(payment.amount)} by {payment.method}; balance {format_money(balance)}")


def cmd_folio(args):
    desk = Desk(args)
    print(folio_print.print_folio(desk.hotel, args.reservation))


def cmd_audit(args):
    desk = Desk(args)
    if args.check:
        for item in night_audit.open_items(desk.hotel) or ["Nothing open"]:
            print(item)
        return
    backups.take_backup(desk.state_path, desk.hotel.business_date)
    result = night_audit.run_audit(desk.hotel, desk.settings, desk.journal_path)
    desk_log.clear_finished_calls(desk.hotel)
    disposed = desk_log.dispose_unclaimed(desk.hotel)
    desk.save()
    print(audit_report.audit_report_text(desk.hotel, result))
    if disposed:
        print(f"Lost property past its hold period: {', '.join(str(item.number) for item in disposed)}")


def cmd_report(args):
    desk = Desk(args)
    day = parse_date(args.date) if args.date else desk.hotel.business_date
    print(render_report(args.name, desk.hotel, day, args.format))


def cmd_revenue(args):
    desk = Desk(args)
    start = parse_date(args.start) if args.start else None
    end = parse_date(args.end) if args.end else None
    print(revenue.revenue_text(revenue.revenue_summary(desk.journal_path, start, end)))


def cmd_cash_up(args):
    desk = Desk(args)
    day = parse_date(args.date) if args.date else desk.hotel.business_date
    print(cashier.cash_up_text(desk.hotel, day))


def cmd_rates(args):
    desk = Desk(args)
    day = parse_date(args.date) if args.date else desk.hotel.business_date
    print(rate_sheet.rate_sheet(desk.hotel, desk.settings, day))


def cmd_guest(args):
    desk = Desk(args)
    if args.action == "save":
        vip = {"yes": True, "no": False}.get(args.vip)
        guest = guests.save_profile(desk.hotel, args.name, email=args.email, phone=args.phone, vip=vip,
                                    notes=args.notes)
        desk.save()
        print(f"Saved {guest.name}")
    elif args.action == "find":
        for guest in guests.find(desk.hotel, args.name):
            print(f"{guest.name}{'  (VIP)' if guest.vip else ''}")
    else:
        print(guest_history.guest_card(desk.hotel, args.name))


def cmd_wake_up(args):
    desk = Desk(args)
    if args.action == "book":
        call = desk_log.book_wake_up(desk.hotel, desk.clock, args.room, parse_timestamp(args.at))
        desk.save()
        print(f"Wake-up for room {call.room} at {call.at.isoformat(timespec='minutes')}")
    elif args.action == "done":
        call = desk_log.mark_called(desk.hotel, desk.clock, args.room)
        desk.save()
        print(f"Room {call.room} called")
    else:
        for call in desk_log.calls_due(desk.hotel, desk.clock, args.minutes):
            print(f"{call.at.isoformat(timespec='minutes')}  room {call.room}")


def cmd_lost(args):
    desk = Desk(args)
    if args.action == "log":
        item = desk_log.log_lost_item(desk.hotel, args.where, args.description)
        desk.save()
        print(f"Logged item {item.number}")
    elif args.action == "return":
        item = desk_log.return_item(desk.hotel, args.number, args.to)
        desk.save()
        print(f"Item {item.number} returned to {item.returned_to}")
    else:
        print(table(("item", "found", "where", "description", "status"),
                    [(item.number, item.found_on.isoformat(), item.where, item.description, item.status)
                     for item in desk.hotel.lost_items]))


def cmd_rooms(args):
    desk = Desk(args)
    rooms = sorted(desk.hotel.rooms.values(), key=lambda room: room.number)
    if args.status:
        rooms = [room for room in rooms if room.status == args.status]
    print(table(("room", "type", "status", "occupied"),
                [(room.number, room.type_code, room.status, "yes" if room.occupied else "no") for room in rooms]))
    print(housekeeping_board.board_summary(desk.hotel))


def cmd_hk_sheets(args):
    desk = Desk(args)
    names = [name.strip() for name in args.attendants.split(",") if name.strip()]
    for name, work in housekeeping.assign(desk.hotel, names).items():
        print(name)
        for room, task in work:
            print(f"  {room}  {task}")


def cmd_housekeeping(args):
    desk = Desk(args)
    room = housekeeping.set_status(desk.hotel, args.room, args.status)
    desk.save()
    print(f"Room {room.number} is {room.status}")


def cmd_add_room(args):
    desk = Desk(args)
    room = rooms_admin.add_room(desk.hotel, args.room, args.type, args.floor)
    desk.save()
    print(f"Added room {room.number} ({room.type_code}) on floor {room.floor}")


def cmd_retype_room(args):
    desk = Desk(args)
    room = rooms_admin.change_room_type(desk.hotel, args.room, args.type)
    desk.save()
    print(f"Room {room.number} is now {room.type_code}")


def cmd_base_rate(args):
    desk = Desk(args)
    room_type = rooms_admin.set_base_rate(desk.hotel, args.type, parse_money(args.amount))
    desk.save()
    print(f"{room_type.code} base rate {format_money(room_type.base_rate)}")


def cmd_import_guests(args):
    desk = Desk(args)
    saved, skipped = guest_import.import_guests(desk.hotel, args.file)
    desk.save()
    print(f"Saved {len(saved)}, skipped {len(skipped)}")
    for line, message in skipped:
        print(f"line {line}: {message}")


def cmd_export_setup(args):
    desk = Desk(args)
    setup.export_setup(desk.hotel, args.file)
    print(f"Wrote the setup of {desk.hotel.name} to {args.file}")


def cmd_import(args):
    desk = Desk(args)
    result = channel_import.import_bookings(desk.hotel, desk.settings, args.file)
    desk.save()
    print(f"Booked {len(result.booked)}, rejected {len(result.rejected)}")
    for line, message in result.rejected:
        print(f"line {line}: {message}")


def cmd_export(args):
    desk = Desk(args)
    day = parse_date(args.date) if args.date else None
    written = folio_export.export_folios(desk.hotel, args.file, day)
    print(f"Wrote {written} charges to {args.file}")


def build_parser():
    parser = argparse.ArgumentParser(prog="hoteldesk", description="Front desk for a small hotel.")
    parser.add_argument("--state", default=DEFAULT_STATE, help="state file (default: %(default)s)")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS, help="settings file (default: %(default)s)")
    parser.add_argument("--now", help="the time the command acts at, as YYYY-MM-DDTHH:MM")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, handler, help_text):
        sub = commands.add_parser(name, help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    sub = command("init", cmd_init, "create the state file from a setup file")
    sub.add_argument("setup")
    sub.add_argument("--business-date", required=True)

    for name, handler, help_text in (("quote", cmd_quote, "price a stay"), ("book", cmd_book, "take a booking")):
        sub = command(name, handler, help_text)
        if name == "book":
            sub.add_argument("--guest", required=True)
        sub.add_argument("--type", required=True)
        sub.add_argument("--arrival", required=True)
        sub.add_argument("--departure", required=True)
        sub.add_argument("--adults", type=int, default=1)
        sub.add_argument("--plan", default=booking.DEFAULT_PLAN)

    sub = command("move-dates", cmd_move_dates, "move a booked stay to new dates")
    sub.add_argument("reservation")
    sub.add_argument("--arrival", required=True)
    sub.add_argument("--departure", required=True)

    command("settings", cmd_settings, "show the settings in force")

    sub = command("extend", cmd_extend, "keep an in-house guest longer")
    sub.add_argument("reservation")
    sub.add_argument("--departure", required=True)

    for name, handler, help_text in (("show", cmd_show, "show a reservation"),
                                     ("cancel", cmd_cancel, "cancel a booking"),
                                     ("checkout", cmd_checkout, "check a guest out"),
                                     ("folio", cmd_folio, "print a folio")):
        command(name, handler, help_text).add_argument("reservation")

    command("reinstate", cmd_reinstate, "take back a no-show who arrived after all").add_argument("reservation")

    sub = command("checkin", cmd_checkin, "check a guest in")
    sub.add_argument("reservation")
    sub.add_argument("--room")

    sub = command("move-room", cmd_move_room, "move an in-house guest to another room")
    sub.add_argument("reservation")
    sub.add_argument("room")

    sub = command("post", cmd_post, "post a charge to a folio")
    sub.add_argument("reservation")
    sub.add_argument("code")
    sub.add_argument("amount")
    sub.add_argument("--description")

    sub = command("transfer", cmd_transfer, "move a charge to another guest's folio")
    sub.add_argument("reservation")
    sub.add_argument("line", type=int, help="the charge's line on the printed folio, from 1")
    sub.add_argument("to")

    sub = command("pay", cmd_pay, "take a payment")
    sub.add_argument("reservation")
    sub.add_argument("amount")
    sub.add_argument("--method", default="card", choices=billing.PAYMENT_METHODS)

    sub = command("audit", cmd_audit, "run the night audit and close the business date")
    sub.add_argument("--check", action="store_true", help="only list what is still open")

    sub = command("report", cmd_report, "print a day report")
    sub.add_argument("name", choices=sorted(REPORTS))
    sub.add_argument("--date", help="default: the business date")
    sub.add_argument("--format", default="text", choices=FORMATS)

    sub = command("revenue", cmd_revenue, "revenue from the audit journal")
    sub.add_argument("--from", dest="start")
    sub.add_argument("--to", dest="end")

    sub = command("cash-up", cmd_cash_up, "payments taken on a day, by method")
    sub.add_argument("--date", help="default: the business date")

    sub = command("rates", cmd_rates, "one night's rate for every room type and plan")
    sub.add_argument("--date", help="default: the business date")

    sub = command("guest", cmd_guest, "guest profiles")
    sub.add_argument("action", choices=("save", "show", "find"))
    sub.add_argument("name")
    sub.add_argument("--email")
    sub.add_argument("--phone")
    sub.add_argument("--vip", choices=("yes", "no"))
    sub.add_argument("--notes")

    wake_up = command("wake-up", cmd_wake_up, "wake-up calls").add_subparsers(dest="action", required=True)
    sub = wake_up.add_parser("book")
    sub.add_argument("room")
    sub.add_argument("at", help="YYYY-MM-DDTHH:MM")
    sub = wake_up.add_parser("due")
    sub.add_argument("--minutes", type=int, default=15)
    wake_up.add_parser("done").add_argument("room")

    lost = command("lost", cmd_lost, "lost property").add_subparsers(dest="action", required=True)
    sub = lost.add_parser("log")
    sub.add_argument("where")
    sub.add_argument("description")
    sub = lost.add_parser("return")
    sub.add_argument("number", type=int)
    sub.add_argument("to")
    lost.add_parser("list")

    sub = command("rooms", cmd_rooms, "list rooms")
    sub.add_argument("--status")

    sub = command("hk", cmd_housekeeping, "set a room's housekeeping status")
    sub.add_argument("room")
    sub.add_argument("status")

    sub = command("hk-sheets", cmd_hk_sheets, "split today's housekeeping between attendants")
    sub.add_argument("attendants", help="names, separated by commas")

    sub = command("add-room", cmd_add_room, "add a room to the hotel")
    sub.add_argument("room")
    sub.add_argument("type")
    sub.add_argument("--floor", type=int)

    sub = command("retype-room", cmd_retype_room, "change a vacant room's type")
    sub.add_argument("room")
    sub.add_argument("type")

    sub = command("base-rate", cmd_base_rate, "set a room type's base rate for new bookings")
    sub.add_argument("type")
    sub.add_argument("amount")

    command("import-guests", cmd_import_guests, "load guest profiles from CSV").add_argument("file")

    sub = command("import", cmd_import, "book the lines of a channel manager file")
    sub.add_argument("file")

    command("export-setup", cmd_export_setup, "write rooms and rate plans as a setup file").add_argument("file")

    sub = command("export-folios", cmd_export, "write folio charges to CSV")
    sub.add_argument("file")
    sub.add_argument("--date")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except HotelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
