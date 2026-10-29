"""The `boxoffice` command line: argument parsing and error reporting."""
import argparse
from pathlib import Path
import sys

from .. import __version__
from ..clock import FixedClock, SystemClock, parse_time
from ..config import SettingsError
from ..errors import BoxOfficeError
from ..reports.formatters import FORMATS
from ..services.boxoffice import BoxOffice
from ..services.sales import PAYMENT_METHODS
from ..storage.schedule_import import ScheduleError
from . import commands


def _moment(text):
    try:
        return parse_time(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def _count(text):
    if not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"expected a positive whole number, got {text!r}")
    return int(text)


def _format_option(parser):
    parser.add_argument("--format", choices=FORMATS, default="text", help="output format (default: text)")


def build_parser():
    parser = argparse.ArgumentParser(prog="boxoffice", description="Box-office ticketing for a small theatre.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--data", default=".", help="data directory (default: the current directory)")
    parser.add_argument("--now", type=_moment, help="act as if it were this time, YYYY-MM-DDTHH:MM")
    commands_parser = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    venue = commands_parser.add_parser("venue", help="install the venue's seat map")
    venue.add_argument("file", help="seat map file")
    venue.set_defaults(handler=commands.install_venue)

    seatmap = commands_parser.add_parser("seatmap", help="print the installed seat map")
    seatmap.set_defaults(handler=commands.show_seatmap)

    perf = commands_parser.add_parser("perf", help="add, import or list performances")
    perf_actions = perf.add_subparsers(dest="action", required=True, metavar="ACTION")
    add = perf_actions.add_parser("add", help="add one performance")
    add.add_argument("code")
    add.add_argument("--title", required=True)
    add.add_argument("--starts", required=True, type=_moment, help="YYYY-MM-DDTHH:MM")
    add.add_argument("--price", action="append", required=True, metavar="TIER=PRICE",
                     help="price for a tier in pounds, e.g. A=32.50; repeat for each tier")
    add.set_defaults(handler=commands.add_performance)
    imported = perf_actions.add_parser("import", help="add performances from a schedule CSV")
    imported.add_argument("file")
    imported.set_defaults(handler=commands.import_performances)
    remove = perf_actions.add_parser("remove", help="remove a performance that has no orders")
    remove.add_argument("code")
    remove.set_defaults(handler=commands.remove_performance)
    reprice = perf_actions.add_parser("reprice", help="change tier prices; sold seats keep their price")
    reprice.add_argument("code")
    reprice.add_argument("--price", action="append", required=True, metavar="TIER=PRICE")
    reprice.set_defaults(handler=commands.reprice_performance)
    shown = perf_actions.add_parser("show", help="one performance: prices, seats left, refund deadline")
    shown.add_argument("code")
    shown.set_defaults(handler=commands.show_performance)
    listed = perf_actions.add_parser("list", help="list performances")
    listed.add_argument("--upcoming", action="store_true", help="only performances not yet started")
    _format_option(listed)
    listed.set_defaults(handler=commands.list_performances)

    seats = commands_parser.add_parser("seats", help="show the seat plan of a performance")
    seats.add_argument("code")
    seats.set_defaults(handler=commands.show_seats)

    prices = commands_parser.add_parser("prices", help="show the price list of a performance")
    prices.add_argument("code")
    _format_option(prices)
    prices.set_defaults(handler=commands.show_prices)

    hold = commands_parser.add_parser("hold", help="hold seats for a customer")
    hold.add_argument("code")
    hold.add_argument("seats", nargs="*", help="seat ids such as A7")
    hold.add_argument("--best", type=_count, metavar="N", help="hold the best N seats together instead")
    hold.add_argument("--section", help="with --best, look only in this section")
    hold.set_defaults(handler=commands.hold_seats)

    release = commands_parser.add_parser("release", help="release a hold")
    release.add_argument("hold")
    release.set_defaults(handler=commands.release_hold)

    sell = commands_parser.add_parser("sell", help="sell the seats of a hold")
    sell.add_argument("hold")
    sell.add_argument("--concession", action="append", default=[], metavar="SEAT=NAME",
                      help="concession for one seat; seats not named are adult")
    sell.add_argument("--payment", choices=PAYMENT_METHODS, default="card")
    sell.add_argument("--customer", metavar="EMAIL", help="the customer's email, from the customer book")
    sell.set_defaults(handler=commands.sell)

    refund = commands_parser.add_parser("refund", help="refund seats of an order, or all of it")
    refund.add_argument("order")
    refund.add_argument("seats", nargs="*", help="seats to refund (default: the whole order)")
    refund.set_defaults(handler=commands.refund)

    exchange = commands_parser.add_parser("exchange", help="move an order to other seats or another performance")
    exchange.add_argument("order")
    exchange.add_argument("--to", required=True, metavar="CODE", help="performance to move to")
    exchange.add_argument("seats", nargs="+", help="the new seats, one for each seat of the order")
    exchange.set_defaults(handler=commands.exchange)

    cancel = commands_parser.add_parser("cancel", help="cancel a performance and refund every order in full")
    cancel.add_argument("code")
    cancel.set_defaults(handler=commands.cancel_performance)

    notices = commands_parser.add_parser("notices", help="letters for customers of a cancelled performance")
    notices.add_argument("code")
    notices.set_defaults(handler=commands.print_notices)

    customer = commands_parser.add_parser("customer", help="the customer book")
    customer_actions = customer.add_subparsers(dest="action", required=True, metavar="ACTION")
    new_customer = customer_actions.add_parser("add", help="add a customer")
    new_customer.add_argument("email")
    new_customer.add_argument("--name", required=True)
    new_customer.add_argument("--phone", default="")
    new_customer.add_argument("--mailing-list", action="store_true", help="they agreed to hear about new shows")
    new_customer.set_defaults(handler=commands.add_customer)
    find = customer_actions.add_parser("find", help="search names, emails and phone numbers")
    find.add_argument("text")
    _format_option(find)
    find.set_defaults(handler=commands.find_customers)
    mailing = customer_actions.add_parser("mailing-list", help="emails of customers on the mailing list")
    mailing.set_defaults(handler=commands.mailing_list)
    mailing_csv = customer_actions.add_parser("export", help="write the mailing list as CSV")
    mailing_csv.add_argument("file")
    mailing_csv.set_defaults(handler=commands.export_mailing_list)
    assign = customer_actions.add_parser("assign", help="attach an order to a customer")
    assign.add_argument("order")
    assign.add_argument("email", nargs="?", help="leave out to detach the order")
    assign.set_defaults(handler=commands.assign_customer)
    history = customer_actions.add_parser("orders", help="a customer's orders")
    history.add_argument("email")
    _format_option(history)
    history.set_defaults(handler=commands.customer_orders)

    waitlist = commands_parser.add_parser("waitlist", help="the waiting list for sold-out performances")
    waitlist_actions = waitlist.add_subparsers(dest="action", required=True, metavar="ACTION")
    join = waitlist_actions.add_parser("join", help="add someone to the waiting list")
    join.add_argument("code")
    join.add_argument("email")
    join.add_argument("--seats", type=_count, default=1)
    join.set_defaults(handler=commands.join_waitlist)
    leave = waitlist_actions.add_parser("leave", help="take someone off the waiting list")
    leave.add_argument("code")
    leave.add_argument("email")
    leave.set_defaults(handler=commands.leave_waitlist)
    contact = waitlist_actions.add_parser("contact", help="who to ring now that seats are free")
    contact.add_argument("code")
    contact.set_defaults(handler=commands.waitlist_contacts)

    orders = commands_parser.add_parser("orders", help="list orders")
    orders.add_argument("--performance", metavar="CODE")
    _format_option(orders)
    orders.set_defaults(handler=commands.list_orders)

    receipt = commands_parser.add_parser("receipt", help="print the receipt for an order")
    receipt.add_argument("order")
    receipt.set_defaults(handler=commands.show_receipt)

    tickets = commands_parser.add_parser("tickets", help="print the tickets of an order")
    tickets.add_argument("order")
    tickets.set_defaults(handler=commands.print_tickets)

    report = commands_parser.add_parser("report", help="sales reports")
    kinds = report.add_subparsers(dest="report", required=True, metavar="REPORT")
    daily = kinds.add_parser("daily", help="takings per day")
    daily.add_argument("--day", help="only this day, YYYY-MM-DD")
    daily.add_argument("--total", action="store_true", help="add a total row")
    _format_option(daily)
    daily.set_defaults(handler=commands.daily_report)
    cash = kinds.add_parser("cashup", help="one day's takings by payment method")
    cash.add_argument("--day", required=True, help="YYYY-MM-DD")
    _format_option(cash)
    cash.set_defaults(handler=commands.cashup_report)
    full = kinds.add_parser("occupancy", help="seats sold by section")
    full.add_argument("code")
    _format_option(full)
    full.set_defaults(handler=commands.occupancy_report)
    door = kinds.add_parser("doorlist", help="who sits where, for front of house")
    door.add_argument("code")
    _format_option(door)
    door.set_defaults(handler=commands.door_list_report)
    season = kinds.add_parser("season", help="every performance with its sales")
    _format_option(season)
    season.set_defaults(handler=commands.season_report)
    house = kinds.add_parser("house", help="the house manager's sheet for a performance")
    house.add_argument("code")
    house.set_defaults(handler=commands.house_report)
    productions = kinds.add_parser("productions", help="sales by production")
    _format_option(productions)
    productions.set_defaults(handler=commands.production_report)
    mix = kinds.add_parser("concessions", help="tickets sold by concession")
    mix.add_argument("code")
    _format_option(mix)
    mix.set_defaults(handler=commands.concession_report)
    hourly = kinds.add_parser("hourly", help="orders by hour of the day")
    hourly.add_argument("--performance", metavar="CODE")
    _format_option(hourly)
    hourly.set_defaults(handler=commands.hourly_report)

    export = commands_parser.add_parser("export", help="export orders to CSV")
    export.add_argument("file")
    export.add_argument("--performance", metavar="CODE")
    export.set_defaults(handler=commands.export_orders)

    check = commands_parser.add_parser("check", help="look for inconsistencies in the data directory")
    check.set_defaults(handler=commands.check_data)

    settings = commands_parser.add_parser("settings", help="show the settings in force")
    settings.set_defaults(handler=commands.show_settings)

    upgrade = commands_parser.add_parser("upgrade", help="bring data files from older releases up to date")
    upgrade.set_defaults(handler=commands.upgrade_data)

    backup = commands_parser.add_parser("backup", help="copy the data files, list or restore copies")
    backup_actions = backup.add_subparsers(dest="action", required=True, metavar="ACTION")
    create = backup_actions.add_parser("create")
    create.add_argument("--name", help="default: the current time")
    create.set_defaults(handler=commands.create_backup)
    backups = backup_actions.add_parser("list")
    backups.set_defaults(handler=commands.list_backups)
    restore = backup_actions.add_parser("restore")
    restore.add_argument("name")
    restore.set_defaults(handler=commands.restore_backup)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    clock = FixedClock(args.now) if args.now else SystemClock()
    try:
        office = BoxOffice(Path(args.data), clock)
        return args.handler(office, args) or 0
    except (BoxOfficeError, SettingsError, ScheduleError, commands.UsageError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
