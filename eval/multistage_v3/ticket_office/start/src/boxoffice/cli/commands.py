"""One handler per command. Each takes the box office and the parsed arguments."""
from pathlib import Path

from datetime import timedelta

from ..clock import format_time
from ..config import describe_settings
from ..model.money import format_pence, parse_price
from ..model.seat_ranges import compress_seats, expand_seats
from ..reports.concession_mix import COLUMNS as MIX_COLUMNS, concession_mix
from ..reports.cashup import COLUMNS as CASHUP_COLUMNS, cashup
from ..reports.daily import COLUMNS as DAILY_COLUMNS, daily_takings, totals
from ..reports.door_list import COLUMNS as DOOR_COLUMNS, door_list
from ..reports.formatters import Column, render
from ..reports.hourly import COLUMNS as HOURLY_COLUMNS, sales_by_hour
from ..reports.house_sheet import house_sheet
from ..reports.notices import cancellation_notices
from ..reports.occupancy import COLUMNS as OCCUPANCY_COLUMNS, occupancy
from ..reports.price_list import price_list
from ..reports.productions import COLUMNS as PRODUCTION_COLUMNS, production_summary
from ..reports.receipt import render_receipt, render_tickets
from ..reports.season import COLUMNS as SEASON_COLUMNS, season_summary
from ..reports.seatplan import count_states, render_seatplan
from ..services.availability import section_summary
from ..storage import backup
from ..storage.csv_export import export_orders as write_orders_csv
from ..storage.mailing_export import export_mailing_list as write_mailing_csv
from ..storage.migrations import upgrade
from ..storage.seatmap_format import format_seatmap

ORDER_COLUMNS = [Column("order"), Column("performance"), Column("seats"), Column("payment"),
                 Column("created"), Column("total", "money")]
PERFORMANCE_COLUMNS = [Column("code"), Column("title"), Column("starts"), Column("prices")]
CUSTOMER_COLUMNS = [Column("email"), Column("name"), Column("phone")]


class UsageError(ValueError):
    """Arguments argparse accepted but the command cannot use."""


def install_venue(office, args):
    venue = office.store.install_venue(Path(args.file).read_text(encoding="utf-8"))
    print(f"venue {venue.name}: {venue.capacity} seats in {len(venue.sections)} sections")


def show_seatmap(office, args):
    venue = office.store.venue()
    print(format_seatmap(venue), end="")
    for section in venue.sections:
        print(f"# {section.name}: {section.capacity} seats")


def add_performance(office, args):
    performance = office.schedule.add(args.code, args.title, args.starts, _prices(args.price))
    print(f"added {performance.code}: {performance.title} at {format_time(performance.starts)}")


def import_performances(office, args):
    added = office.schedule.import_file(args.file)
    print(f"added {len(added)} performances")


def remove_performance(office, args):
    office.schedule.remove(args.code)
    print(f"removed {args.code}")


def reprice_performance(office, args):
    performance = office.schedule.reprice(args.code, _prices(args.price))
    print(f"{performance.code}: {_price_text(performance.prices)}")


def show_performance(office, args):
    performance = office.store.performance(args.code)
    counts = count_states(office.seat_states(args.code))
    sections = section_summary(office.store, args.code, office.clock.now())
    deadline = performance.starts - timedelta(hours=office.settings.refund_cutoff_hours)
    print(f"{performance.code}: {performance.title}" + (" (cancelled)" if performance.cancelled else ""))
    print(f"starts   {format_time(performance.starts)}")
    print(f"prices   {_price_text(performance.prices)}")
    print("seats    " + ", ".join(f"{state} {count}" for state, count in counts.items()))
    for name, section_counts in sections.items():
        print(f"  {name:<10} " + ", ".join(f"{state} {count}" for state, count in section_counts.items()))
    print(f"refunds  until {format_time(deadline)}")


def list_performances(office, args):
    since = office.clock.now() if args.upcoming else None
    rows = [{"code": performance.code, "title": performance.title,
             "starts": format_time(performance.starts),
             "prices": _price_text(performance.prices)}
            for performance in office.schedule.listing(since)]
    print(render(PERFORMANCE_COLUMNS, rows, args.format))


def show_seats(office, args):
    states = office.seat_states(args.code)
    print(render_seatplan(office.store.venue(), states))
    print(", ".join(f"{state} {count}" for state, count in count_states(states).items()))


def show_prices(office, args):
    columns, rows = price_list(office.store.performance(args.code), office.store.venue())
    print(render(columns, rows, args.format))


def hold_seats(office, args):
    if args.best and args.seats:
        raise UsageError("name seats or use --best, not both")
    if args.best:
        hold = office.holds.place_best(args.code, args.best, section=args.section)
    else:
        hold = office.holds.place(args.code, expand_seats(args.seats))
    print(f"hold {hold.id}: {' '.join(hold.seats)} until {format_time(hold.expires)}")


def release_hold(office, args):
    hold = office.holds.release(args.hold)
    print(f"released {hold.id}: {compress_seats(hold.seats)}")


def sell(office, args):
    concessions = dict(_pair(text, "--concession") for text in args.concession)
    order = office.sales.checkout(args.hold, concessions, payment=args.payment, customer=args.customer)
    print(f"order {order.id}: {len(order.lines)} tickets, total {format_pence(order.total)}")


def refund(office, args):
    amount = office.refunds.refund(args.order, expand_seats(args.seats) or None)
    print(f"refunded {format_pence(amount)} on order {args.order}")


def exchange(office, args):
    amount = office.refunds.exchange(args.order, args.to, expand_seats(args.seats))
    print(f"exchanged order {args.order} to {args.to}: settled {format_pence(amount)}")


def cancel_performance(office, args):
    count, paid_back = office.refunds.cancel_performance(args.code)
    print(f"cancelled {args.code}: refunded {format_pence(paid_back)} on {count} orders")


def print_notices(office, args):
    performance = office.store.performance(args.code)
    notices = cancellation_notices(performance, office.store.load_orders(), office.customers.all(),
                                   office.settings.theatre)
    for email, text in notices:
        print(f"To: {email}\n\n{text}\n")
    print(f"{len(notices)} notices")


def add_customer(office, args):
    customer = office.customers.add(args.email, args.name, args.phone, args.mailing_list)
    print(f"added {customer.name} <{customer.email}>")


def find_customers(office, args):
    rows = [{"email": customer.email, "name": customer.name, "phone": customer.phone}
            for customer in office.customers.search(args.text)]
    print(render(CUSTOMER_COLUMNS, rows, args.format))


def mailing_list(office, args):
    for email in office.customers.mailing_list():
        print(email)


def export_mailing_list(office, args):
    count = write_mailing_csv(office.customers.all(), args.file)
    print(f"exported {count} customers to {args.file}")


def assign_customer(office, args):
    order = office.sales.assign_customer(args.order, args.email)
    print(f"order {order.id}: " + (f"customer {order.customer}" if order.customer else "no customer"))


def customer_orders(office, args):
    email = office.customers.get(args.email).email
    orders = {key: order for key, order in office.store.load_orders().items() if order.customer == email}
    print(render(ORDER_COLUMNS, _order_rows(orders), args.format))


def join_waitlist(office, args):
    position = office.waitlist.join(args.code, args.email, args.seats)
    print(f"{args.email} is number {position} waiting for {args.code}")


def leave_waitlist(office, args):
    office.waitlist.leave(args.code, args.email)
    print(f"{args.email} is no longer waiting for {args.code}")


def waitlist_contacts(office, args):
    for entry in office.waitlist.to_contact(args.code):
        print(f"{entry['email']}: {entry['seats']} seats")


def list_orders(office, args):
    orders = {key: order for key, order in office.store.load_orders().items()
              if args.performance in (None, order.performance)}
    print(render(ORDER_COLUMNS, _order_rows(orders), args.format))


def show_receipt(office, args):
    order = office.order(args.order)
    performance = office.store.performance(order.performance)
    print(render_receipt(order, performance, office.store.venue(), office.settings))


def print_tickets(office, args):
    order = office.order(args.order)
    performance = office.store.performance(order.performance)
    print(render_tickets(order, performance, office.store.venue(), office.settings.theatre))


def daily_report(office, args):
    rows = daily_takings(office.ledger.read_entries(), args.day)
    if args.total:
        rows.append(totals(rows))
    print(render(DAILY_COLUMNS, rows, args.format))


def cashup_report(office, args):
    print(render(CASHUP_COLUMNS, cashup(office.ledger.entries_on(args.day)), args.format))


def occupancy_report(office, args):
    office.store.performance(args.code)
    rows = occupancy(office.store.venue(), office.store.load_orders(), args.code)
    print(render(OCCUPANCY_COLUMNS, rows, args.format))


def door_list_report(office, args):
    office.store.performance(args.code)
    rows = door_list(office.store.venue(), office.store.load_orders(), office.customers.all(), args.code)
    print(render(DOOR_COLUMNS, rows, args.format))


def house_report(office, args):
    performance = office.store.performance(args.code)
    print(house_sheet(performance, office.store.venue(), office.store.load_orders(), office.customers.all()))


def concession_report(office, args):
    office.store.performance(args.code)
    print(render(MIX_COLUMNS, concession_mix(office.store.load_orders(), args.code), args.format))


def hourly_report(office, args):
    print(render(HOURLY_COLUMNS, sales_by_hour(office.store.load_orders(), args.performance), args.format))


def production_report(office, args):
    rows = production_summary(office.store.performances(), office.store.load_orders(),
                              office.store.venue().capacity)
    print(render(PRODUCTION_COLUMNS, rows, args.format))


def season_report(office, args):
    rows = season_summary(office.store.performances(), office.store.load_orders(), office.store.venue().capacity)
    print(render(SEASON_COLUMNS, rows, args.format))


def export_orders(office, args):
    count = write_orders_csv(office.store.load_orders(), args.file, args.performance)
    print(f"exported {count} seats to {args.file}")


def check_data(office, args):
    problems = office.check()
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("no problems found")


def show_settings(office, args):
    for name, value, source in describe_settings(office.root):
        print(f"{name} = {value}  ({source})")


def upgrade_data(office, args):
    changed = upgrade(office.root)
    print(f"upgraded {', '.join(changed)}" if changed else "already up to date")


def create_backup(office, args):
    name = args.name or format_time(office.clock.now()).replace(":", "")
    copied = backup.create_backup(office.root, name)
    print(f"backup {name}: {len(copied)} files")


def list_backups(office, args):
    for name in backup.list_backups(office.root):
        print(name)


def restore_backup(office, args):
    backup.restore_backup(office.root, args.name)
    print(f"restored backup {args.name}")


def _order_rows(orders):
    return [{"order": order.id, "performance": order.performance,
             "seats": compress_seats([line.seat for line in order.active_lines()]),
             "payment": order.payment, "created": format_time(order.created), "total": order.total}
            for order in sorted(orders.values(), key=lambda order: order.id)]


def _price_text(prices):
    return " ".join(f"{tier}={format_pence(price)}" for tier, price in sorted(prices.items()))


def _prices(texts):
    prices = {}
    for text in texts:
        tier, price = _pair(text, "--price")
        try:
            prices[tier] = parse_price(price)
        except ValueError as error:
            raise UsageError(f"--price {text}: {error}") from None
    return prices


def _pair(text, option):
    key, sep, value = text.partition("=")
    if not sep or not key or not value:
        raise UsageError(f"{option} expects KEY=VALUE, got {text!r}")
    return key, value
