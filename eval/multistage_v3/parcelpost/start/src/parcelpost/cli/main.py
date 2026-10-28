"""The `parcelpost` command."""
import argparse
from pathlib import Path
import sys

from ..config import load_settings
from ..core.accounts import DEFAULT_PAYMENT_DAYS, make_account
from ..core.address import make_address, normalise_postcode
from ..core.clock import FixedClock, SystemClock, parse_day, parse_timestamp
from ..core.errors import ParcelpostError, UnknownShipment, ValidationError
from ..core.money import format_amount, parse_amount
from ..core.parcel import Parcel
from ..core.shipment import STATUSES
from ..core.units import kg_to_grams, parse_size
from ..rating.tariff import service_name
from ..rating.zones import areas_by_zone
from ..reports.daily import daily_summary, render_daily
from ..reports.export import export_shipments
from ..reports.ratecard import render_rate_card
from ..reports.performance import on_time_performance, render_performance
from ..reports.stalled import find_stalled, render_stalled
from ..reports.statement import account_statement, render_statement
from ..reports.zones import render_zone_totals, zone_totals
from ..services.billing import bill_day
from ..services.claims import REASONS, claims_since, raise_claim
from ..services.booking import (Order, book, expected_delivery, label_path, quote_every_service,
                                quote_parcel, void)
from ..services.housekeeping import archive_finished, check_data
from ..services.importer import import_orders
from ..services.manifesting import close_day
from ..services.pickup import pickup_text, request_pickup
from ..services.reconcile import reconcile
from ..services.returns import book_return
from ..services.scans import import_scans
from ..services.tracking import track
from ..storage.accounts import AccountBook
from ..storage.addressbook import AddressBook
from ..storage.files import write_atomic
from ..storage.shipments import ShipmentStore
from . import output

EXIT_ERROR = 1
EXIT_NOT_FOUND = 3
DAY_HELP = "collection day, YYYY-MM-DD; today when omitted"


def build_parser():
    parser = argparse.ArgumentParser(prog="parcelpost", description="Quote, book, track and bill parcels.")
    parser.add_argument("--data-dir", default=".parcelpost",
                        help="where shipments, manifests, labels and invoices are kept")
    parser.add_argument("--now", help="current time as YYYY-MM-DDTHH:MM instead of the system clock")
    commands = parser.add_subparsers(dest="command", required=True)

    quoting = commands.add_parser("quote", help="price a parcel")
    quoting.add_argument("--to", required=True, metavar="POSTCODE")
    quoting.add_argument("--service", help="price one service instead of all of them")
    _parcel_options(quoting)

    booking = commands.add_parser("book", help="book a shipment and write its label")
    booking.add_argument("--account", required=True)
    booking.add_argument("--recipient", metavar="ALIAS", help="a saved address instead of the four below")
    booking.add_argument("--name")
    booking.add_argument("--address", help="first line of the address")
    booking.add_argument("--town")
    booking.add_argument("--to", metavar="POSTCODE")
    booking.add_argument("--service", help="defaults to the default_service setting")
    _parcel_options(booking)

    voiding = commands.add_parser("void", help="cancel a shipment that is not yet manifested")
    voiding.add_argument("number")

    returning = commands.add_parser("return", help="book the return of a delivered shipment")
    returning.add_argument("number")

    listing = commands.add_parser("list", help="list shipments")
    listing.add_argument("--day", help="collection day, YYYY-MM-DD")
    listing.add_argument("--status", choices=STATUSES)
    listing.add_argument("--account")

    tracking = commands.add_parser("track", help="show a shipment's status and scans")
    tracking.add_argument("number")

    scanning = commands.add_parser("scan", help="record the carrier's scan file")
    scanning.add_argument("file", type=Path)

    pickup = commands.add_parser("pickup", help="request a collection from the depot")
    pickup.add_argument("--day", help=DAY_HELP)

    manifest = commands.add_parser("manifest", help="close a collection day and write its manifest")
    manifest.add_argument("--day", help=DAY_HELP)

    billing = commands.add_parser("bill", help="invoice every account on a closed day")
    billing.add_argument("--day", help=DAY_HELP)

    reconciling = commands.add_parser("reconcile", help="check the carrier's invoice against a manifest")
    reconciling.add_argument("file", type=Path)
    reconciling.add_argument("--day", help=DAY_HELP)

    report = commands.add_parser("report", help="print a report")
    report.add_argument("name", choices=sorted(REPORTS))
    report.add_argument("--day", help="collection day for the daily report; today when omitted")
    report.add_argument("--from", dest="start", help="first day of the period, YYYY-MM-DD")
    report.add_argument("--to", dest="end", help="last day of the period, YYYY-MM-DD; today when omitted")

    statement = commands.add_parser("statement", help="an account's shipments over a period")
    statement.add_argument("--account", required=True)
    statement.add_argument("--from", dest="start", required=True)
    statement.add_argument("--to", dest="end", help="today when omitted")

    exporting = commands.add_parser("export", help="CSV of shipments collected over a period")
    exporting.add_argument("--from", dest="start", required=True)
    exporting.add_argument("--to", dest="end", help="today when omitted")
    exporting.add_argument("--output", type=Path, help="file to write; standard output when omitted")

    orders = commands.add_parser("import", help="book every order in a web shop orders file")
    orders.add_argument("file", type=Path)

    accounts = commands.add_parser("account", help="register or list customer accounts")
    account_commands = accounts.add_subparsers(dest="action", required=True)
    adding = account_commands.add_parser("add", help="register an account")
    adding.add_argument("code")
    adding.add_argument("--name", required=True)
    adding.add_argument("--email", required=True, help="where invoices are sent")
    adding.add_argument("--payment-days", type=int, default=DEFAULT_PAYMENT_DAYS)
    account_commands.add_parser("list", help="list registered accounts")

    claiming = commands.add_parser("claim", help="claim for a lost or damaged parcel")
    claiming.add_argument("number")
    claiming.add_argument("--reason", required=True, choices=REASONS)

    claims = commands.add_parser("claims", help="list claims raised since a day")
    claims.add_argument("--since", required=True, help="YYYY-MM-DD")

    archiving = commands.add_parser("archive", help="move finished shipments out of the store")
    archiving.add_argument("--before", required=True, help="collection days before this one, YYYY-MM-DD")

    commands.add_parser("check", help="look for missing labels, manifests and scans")

    addresses = commands.add_parser("address", help="save or list an account's recipients")
    address_commands = addresses.add_subparsers(dest="action", required=True)
    saving = address_commands.add_parser("add", help="save a recipient under an alias")
    saving.add_argument("account")
    saving.add_argument("alias")
    saving.add_argument("--name", required=True)
    saving.add_argument("--address", required=True, help="first line of the address")
    saving.add_argument("--town", required=True)
    saving.add_argument("--to", required=True, metavar="POSTCODE")
    showing = address_commands.add_parser("list", help="list an account's saved recipients")
    showing.add_argument("account")

    rates = commands.add_parser("rates", help="print a service's rate card")
    rates.add_argument("service")

    commands.add_parser("settings", help="print the settings in effect")

    commands.add_parser("zones", help="list postcode areas by zone")
    return parser


def _parcel_options(parser):
    parser.add_argument("--weight", required=True, help="kilograms, up to three decimals")
    parser.add_argument("--size", default="20x15x10", help="LxWxH in centimetres")
    parser.add_argument("--value", default="0.00", help="declared value in pounds")
    parser.add_argument("--residential", action="store_true", help="deliver to a home address")
    parser.add_argument("--signature", action="store_true", help="require a signature on delivery")


def _parcel(args):
    length, width, height = parse_size(args.size)
    return Parcel(kg_to_grams(args.weight), length, width, height, parse_amount(args.value))


def _day(args, clock):
    return parse_day(args.day) if args.day else clock.now().date()


def _period(args, clock):
    if not args.start:
        raise ValidationError("--from is required for this report")
    start = parse_day(args.start)
    end = parse_day(args.end) if args.end else clock.now().date()
    if end < start:
        raise ValidationError(f"period ends before it starts: {start.isoformat()} to {end.isoformat()}")
    return start, end


def _print_booked(shipment):
    print(f"booked {shipment.tracking_number} {shipment.service} {format_amount(shipment.total)}")


def _quote(args, settings, clock):
    parcel, postcode = _parcel(args), normalise_postcode(args.to)
    options = {"residential": args.residential, "signature": args.signature}
    if args.service:
        quotes = [quote_parcel(settings, parcel, postcode, args.service, **options)]
    else:
        quotes = quote_every_service(settings, parcel, postcode, **options)
    now = clock.now()
    print("\n\n".join(output.quote_text(found, service_name(found.service),
                                          expected_delivery(settings, found.service, now))
                        for found in quotes))


def _recipient(args, settings, account):
    if args.recipient:
        return AddressBook(settings.addresses_path).lookup(account, args.recipient)
    if not (args.name and args.address and args.town and args.to):
        raise ValidationError("give --recipient, or all of --name, --address, --town and --to")
    return make_address(args.name, args.address, args.town, args.to)


def _book(args, settings, clock):
    account = args.account.upper()
    order = Order(
        account=account,
        recipient=_recipient(args, settings, account),
        parcel=_parcel(args),
        service=args.service,
        residential=args.residential,
        signature=args.signature,
    )
    shipment = book(settings, order, clock=clock)
    _print_booked(shipment)
    print(f"ships {shipment.ship_date.isoformat()}, expected {shipment.expected_delivery.isoformat()}")
    print(f"label {label_path(settings, shipment)}")


def _void(args, settings, clock):
    print(f"voided {void(settings, args.number).tracking_number}")


def _return(args, settings, clock):
    shipment = book_return(settings, args.number, clock=clock)
    _print_booked(shipment)
    print(f"label {label_path(settings, shipment)}")


def _list(args, settings, clock):
    shipments = ShipmentStore(settings.store_path).find(
        ship_date=parse_day(args.day) if args.day else None,
        status=args.status,
        account=args.account.upper() if args.account else None)
    print(output.shipments_table(shipments) if shipments else "No shipments.")


def _track(args, settings, clock):
    print(output.tracking_text(track(settings, args.number), clock.now().date()))


def _scan(args, settings, clock):
    recorded = import_scans(settings, args.file.read_text(encoding="utf-8"))
    print(f"recorded {recorded.scans} scans for {recorded.shipments} shipments")


def _pickup(args, settings, clock):
    print(pickup_text(request_pickup(settings, _day(args, clock))), end="")


def _manifest(args, settings, clock):
    closed = close_day(settings, _day(args, clock))
    print(f"manifest {closed.path} with {closed.shipments} shipments")


def _bill(args, settings, clock):
    print(output.invoices_table(bill_day(settings, _day(args, clock))))


def _reconcile(args, settings, clock):
    result = reconcile(settings, _day(args, clock), args.file.read_text(encoding="utf-8"))
    print(output.reconciliation_text(result))
    return 0 if result.balanced else EXIT_ERROR


def _daily_report(args, settings, clock):
    print(render_daily(daily_summary(settings, _day(args, clock))))


def _stalled_report(args, settings, clock):
    print(render_stalled(find_stalled(settings, clock.now()), settings.stale_hours))


def _performance_report(args, settings, clock):
    start, end = _period(args, clock)
    print(render_performance(on_time_performance(settings, start, end), start, end))


def _zones_report(args, settings, clock):
    start, end = _period(args, clock)
    print(render_zone_totals(zone_totals(settings, start, end), start, end))


REPORTS = {
    "daily": _daily_report,
    "stalled": _stalled_report,
    "performance": _performance_report,
    "zones": _zones_report,
}


def _report(args, settings, clock):
    REPORTS[args.name](args, settings, clock)


def _statement(args, settings, clock):
    start, end = _period(args, clock)
    print(render_statement(account_statement(settings, args.account.upper(), start, end)))


def _export(args, settings, clock):
    start, end = _period(args, clock)
    text = export_shipments(settings, start, end)
    if args.output:
        write_atomic(args.output, text)
        print(f"exported to {args.output}")
    else:
        print(text, end="")


def _import(args, settings, clock):
    imported = import_orders(settings, args.file.read_text(encoding="utf-8"), clock=clock)
    for shipment in imported.booked:
        _print_booked(shipment)
    for line, message in imported.errors:
        print(f"line {line}: {message}", file=sys.stderr)
    return EXIT_ERROR if imported.errors else 0


def _account(args, settings, clock):
    accounts = AccountBook(settings.accounts_path)
    if args.action == "add":
        account = make_account(args.code.upper(), args.name, args.email, args.payment_days)
        accounts.add(account)
        accounts.save()
        print(f"added account {account.code}")
    else:
        print(output.accounts_table(accounts.all()) if accounts.all() else "No accounts registered.")


def _claim(args, settings, clock):
    claim = raise_claim(settings, args.number, args.reason, clock=clock)
    print(f"claim {claim.number} for {claim.tracking_number}: {format_amount(claim.pence)}")


def _claims(args, settings, clock):
    claims = claims_since(settings, parse_day(args.since))
    print(output.claims_table(claims) if claims else "No claims.")


def _archive(args, settings, clock):
    print(f"archived {archive_finished(settings, parse_day(args.before))} shipments")


def _check(args, settings, clock):
    problems = check_data(settings)
    for problem in problems:
        print(problem)
    if not problems:
        print("No problems found.")
    return EXIT_ERROR if problems else 0


def _address(args, settings, clock):
    addresses = AddressBook(settings.addresses_path)
    account = args.account.upper()
    if args.action == "add":
        addresses.save_address(account, args.alias, make_address(args.name, args.address, args.town, args.to))
        addresses.save()
        print(f"saved {args.alias} for {account}")
    else:
        saved = addresses.aliases(account)
        print("\n".join(f"{alias}: {', '.join(address.lines())}" for alias, address in saved)
              if saved else f"No saved addresses for {account}.")


def _rates(args, settings, clock):
    print(render_rate_card(args.service.lower()))


def _settings(args, settings, clock):
    print(output.settings_text(settings))


def _zones(args, settings, clock):
    print(output.zones_text(areas_by_zone()))


COMMANDS = {
    "quote": _quote,
    "book": _book,
    "void": _void,
    "return": _return,
    "list": _list,
    "track": _track,
    "scan": _scan,
    "pickup": _pickup,
    "manifest": _manifest,
    "bill": _bill,
    "reconcile": _reconcile,
    "report": _report,
    "statement": _statement,
    "export": _export,
    "import": _import,
    "account": _account,
    "address": _address,
    "claim": _claim,
    "claims": _claims,
    "archive": _archive,
    "check": _check,
    "rates": _rates,
    "settings": _settings,
    "zones": _zones,
}


def main(argv=None, *, clock=None):
    args = build_parser().parse_args(argv)
    try:
        if args.now:
            clock = FixedClock(parse_timestamp(args.now))
        settings = load_settings(args.data_dir)
        return COMMANDS[args.command](args, settings, clock or SystemClock()) or 0
    except UnknownShipment as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_NOT_FOUND
    except ParcelpostError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
