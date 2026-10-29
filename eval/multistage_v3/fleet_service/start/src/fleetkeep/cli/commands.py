"""What each command does. Every command gets the parsed arguments and the clock."""
import json

from ..importers.fuelcard import import_fuel_card
from ..importers.history import import_history
from ..importers.telematics import import_telematics
from ..importers.timesheets import import_timesheet
from ..importers.vehicles import import_vehicles
from ..model.dates import Period, parse_date
from ..model.money import format_money, parse_money
from ..model.readings import FuelEntry, OdometerReading, parse_gallons, parse_odometer
from ..model.vehicle import Vehicle, normalise_vehicle_id
from ..model.workorder import parse_hours
from ..reports.costs import cost_rows
from ..reports.downtime import downtime_rows
from ..reports.due import due_rows
from ..reports.fuel import fuel_rows
from ..reports.orders import defect_rows, history_rows, order_rows
from ..reports.render import render
from ..reports.spend import spend_rows
from ..reports.stock import stock_rows
from ..reports.vehicles import catalog_rows, vehicle_rows
from ..services import workorders
from ..services.checks import run_checks
from ..services.inspections import latest_treads, record_tread, report_defect
from ..services.projection import projected_day
from ..services.reminders import reminders
from ..services.scheduling import due_items
from ..storage.fleetdir import FleetDirectory


NEXT_SERVICES = 3


def _day(text, clock):
    return parse_date(text) if text else clock.today()


def _period(args):
    return Period(parse_date(args.start), parse_date(args.end))


def _print_import(result):
    print(result.summary())
    for line, reason in result.skipped:
        print(f"line {line}: skipped: {reason}")
    for line, reason in result.rejected:
        print(f"line {line}: rejected: {reason}")


class Session:
    """The fleet directory a command works on, loaded once and saved if changed."""

    def __init__(self, args):
        self.directory = FleetDirectory(args.fleet)
        self.fleet = self.directory.load()

    def save(self):
        self.directory.save(self.fleet)


# Setting up


def cmd_init(args, clock):
    FleetDirectory(args.fleet).create(args.name)
    print(f"created fleet {args.name} in {args.fleet}")
    return 0


def cmd_vehicle_add(args, clock):
    session = Session(args)
    vehicle = Vehicle(normalise_vehicle_id(args.id), args.vehicle_class, args.make, args.model,
                      args.year, parse_date(args.in_service), parse_odometer(args.odometer))
    session.fleet.add_vehicle(vehicle)
    session.save()
    print(f"added {vehicle.id} ({vehicle.description})")
    return 0


def cmd_vehicle_import(args, clock):
    session = Session(args)
    result = import_vehicles(session.fleet, args.file)
    session.save()
    _print_import(result)
    return 0


def cmd_vehicle_retire(args, clock):
    session = Session(args)
    vehicle = session.fleet.retire_vehicle(normalise_vehicle_id(args.id), _day(args.on, clock))
    session.save()
    print(f"retired {vehicle.id} on {vehicle.retired.isoformat()}")
    return 0


def cmd_vehicle_show(args, clock):
    session = Session(args)
    fleet, as_of = session.fleet, _day(args.as_of, clock)
    vehicle = fleet.vehicle(normalise_vehicle_id(args.id))
    print(f"{vehicle.id}  {vehicle.description} ({vehicle.vehicle_class})")
    print(f"in service {vehicle.in_service.isoformat()}, odometer {fleet.odometer_on(vehicle.id, as_of)}")
    for order in fleet.orders(vehicle.id):
        if order.is_open:
            print(f"in the shop: {order.id} since {order.opened.isoformat()}")
    for defect in fleet.defects(vehicle.id):
        if defect.is_open:
            print(f"defect {defect.id} ({defect.severity}): {defect.description}")
    upcoming = sorted(((projected_day(fleet, item, as_of), item)
                       for item in due_items(fleet, as_of, vehicle.id)),
                      key=lambda pair: (pair[0] is None, pair[0] or as_of, pair[1].code))
    print("next services:")
    for day, item in upcoming[:NEXT_SERVICES]:
        when = day.isoformat() if day else "not known"
        print(f"  {item.code:<11} {item.service:<32} {item.status:<9} around {when}")
    return 0


def cmd_vehicles(args, clock):
    session = Session(args)
    print(render("vehicles", vehicle_rows(session.fleet, _day(args.as_of, clock)), args.format), end="")
    return 0


def cmd_catalog(args, clock):
    print(render("catalog", catalog_rows(args.vehicle_class), args.format), end="")
    return 0


# Readings and fuel


def cmd_odometer_add(args, clock):
    session = Session(args)
    reading = OdometerReading(normalise_vehicle_id(args.id), _day(args.on, clock),
                              parse_odometer(args.value))
    session.fleet.add_reading(reading)
    session.save()
    print(f"{reading.vehicle_id}: {reading.odometer} miles on {reading.day.isoformat()}")
    return 0


def cmd_odometer_fix(args, clock):
    session = Session(args)
    reading = session.fleet.correct_reading(normalise_vehicle_id(args.id), parse_date(args.on),
                                            parse_odometer(args.value))
    session.save()
    print(f"{reading.vehicle_id}: {reading.odometer} miles on {reading.day.isoformat()}")
    return 0


def cmd_odometer_import(args, clock):
    session = Session(args)
    result = import_telematics(session.fleet, args.file)
    session.save()
    _print_import(result)
    return 0


def cmd_odometer_list(args, clock):
    session = Session(args)
    for reading in session.fleet.readings(normalise_vehicle_id(args.id)):
        print(f"{reading.day.isoformat()}  {reading.odometer:>8}")
    return 0


def cmd_fuel_add(args, clock):
    session = Session(args)
    entry = FuelEntry(normalise_vehicle_id(args.id), _day(args.on, clock), parse_gallons(args.gallons),
                      parse_money(args.cost), parse_odometer(args.odometer) if args.odometer else None)
    session.fleet.add_fuel(entry)
    session.save()
    print(f"{entry.vehicle_id}: {entry.gallons} gallons for {format_money(entry.cost)}")
    return 0


def cmd_fuel_import(args, clock):
    session = Session(args)
    result = import_fuel_card(session.fleet, args.file)
    session.save()
    _print_import(result)
    return 0


def cmd_fuel_card(args, clock):
    session = Session(args)
    session.fleet.assign_card(args.card, normalise_vehicle_id(args.id))
    session.save()
    print(f"card {args.card} fills {session.fleet.card_vehicle(args.card)}")
    return 0


def cmd_fuel_list(args, clock):
    session = Session(args)
    for entry in session.fleet.fuel(normalise_vehicle_id(args.id)):
        odometer = "-" if entry.odometer is None else entry.odometer
        print(f"{entry.day.isoformat()}  {entry.gallons:>8} gal  {format_money(entry.cost):>9}  {odometer:>8}")
    return 0


def cmd_fuel_report(args, clock):
    session = Session(args)
    print(render("fuel", fuel_rows(session.fleet, _period(args)), args.format), end="")
    return 0


# Service history


def cmd_history_import(args, clock):
    session = Session(args)
    result = import_history(session.fleet, args.file)
    session.save()
    _print_import(result)
    return 0


def cmd_history_show(args, clock):
    session = Session(args)
    vehicle = session.fleet.vehicle(normalise_vehicle_id(args.id))
    print(render("history", history_rows(session.fleet, vehicle.id), args.format), end="")
    return 0


# Work orders


def cmd_wo_open(args, clock):
    session = Session(args)
    order = workorders.open_order(session.fleet, normalise_vehicle_id(args.id),
                                  _day(args.on, clock), args.service, args.note, args.breakdown,
                                  [defect.upper() for defect in args.defect])
    session.save()
    print(order.id)
    return 0


def cmd_wo_cancel(args, clock):
    session = Session(args)
    workorders.cancel_order(session.fleet, args.order.upper())
    session.save()
    print(f"cancelled {args.order.upper()}")
    return 0


def cmd_wo_part(args, clock):
    session = Session(args)
    price = parse_money(args.price) if args.price else None
    line = workorders.add_part(session.fleet, args.order.upper(), args.number, args.qty, price,
                               args.description)
    session.save()
    print(f"{line.quantity} x {line.number} at {format_money(line.unit_price)} "
          f"= {format_money(line.amount)}")
    return 0


def cmd_wo_labour(args, clock):
    session = Session(args)
    rate = parse_money(args.rate) if args.rate else None
    line = workorders.log_labour(session.fleet, args.order.upper(), args.mechanic,
                                 parse_hours(args.hours), rate)
    session.save()
    print(f"{line.hours} hours at {format_money(line.rate)} = {format_money(line.amount)}")
    return 0


def cmd_wo_close(args, clock):
    session = Session(args)
    odometer = parse_odometer(args.odometer) if args.odometer else None
    order = workorders.close_order(session.fleet, args.order.upper(), _day(args.on, clock), odometer)
    session.save()
    print(f"closed {order.id} on {order.closed.isoformat()}")
    return 0


def _order_fields(order):
    charges = workorders.order_charges(order)
    return {
        "id": order.id,
        "vehicle": order.vehicle_id,
        "status": order.status,
        "opened": order.opened.isoformat(),
        "closed": order.closed.isoformat() if order.closed else None,
        "services": list(order.services),
        "note": order.note,
        "breakdown": order.breakdown,
        "parts": format_money(charges.parts),
        "labour": format_money(charges.labour),
        "total": format_money(charges.total),
    }


def cmd_wo_show(args, clock):
    session = Session(args)
    order = session.fleet.order(args.order.upper())
    fields = _order_fields(order)
    if args.json:
        print(json.dumps(fields, indent=2))
        return 0
    for name, value in fields.items():
        if isinstance(value, list):
            value = ", ".join(value)
        print(f"{name + ':':<10} {'-' if value in (None, '') else value}")
    for part in order.parts:
        print(f"  part    {part.number} {part.description} x{part.quantity} "
              f"@ {format_money(part.unit_price)}")
    for labour in order.labour:
        print(f"  labour  {labour.mechanic} {labour.hours}h @ {format_money(labour.rate)}")
    return 0


def cmd_wo_list(args, clock):
    session = Session(args)
    vehicle_id = normalise_vehicle_id(args.vehicle) if args.vehicle else None
    print(render("orders", order_rows(session.fleet, vehicle_id, args.open), args.format), end="")
    return 0


def cmd_parts_receive(args, clock):
    session = Session(args)
    item = workorders.receive_parts(session.fleet, args.number, args.qty, parse_money(args.cost),
                                    args.description)
    session.save()
    print(f"{item.number}: {item.on_hand} on hand at {format_money(item.unit_cost)}")
    return 0


def cmd_parts_count(args, clock):
    session = Session(args)
    item = workorders.count_stock(session.fleet, args.number, args.on_hand)
    session.save()
    print(f"{item.number}: {item.on_hand} on hand")
    return 0


def cmd_parts_stock(args, clock):
    session = Session(args)
    print(render("stock", stock_rows(session.fleet), args.format), end="")
    return 0


def cmd_defect_report(args, clock):
    session = Session(args)
    defect = report_defect(session.fleet, normalise_vehicle_id(args.id), _day(args.on, clock),
                           args.description, args.severity)
    session.save()
    print(defect.id)
    return 0


def cmd_defect_list(args, clock):
    session = Session(args)
    vehicle_id = normalise_vehicle_id(args.vehicle) if args.vehicle else None
    print(render("defects", defect_rows(session.fleet, vehicle_id, args.open), args.format), end="")
    return 0


def cmd_tyre_add(args, clock):
    session = Session(args)
    reading = record_tread(session.fleet, normalise_vehicle_id(args.id), _day(args.on, clock),
                           args.position, args.depth)
    session.save()
    print(f"{reading.vehicle_id} {reading.position}: {reading.depth}/32")
    return 0


def cmd_tyre_list(args, clock):
    session = Session(args)
    for reading in latest_treads(session.fleet, normalise_vehicle_id(args.id), _day(args.as_of, clock)):
        print(f"{reading.position:<4} {reading.depth:>2}/32  {reading.day.isoformat()}")
    return 0


def cmd_timesheet_import(args, clock):
    session = Session(args)
    result = import_timesheet(session.fleet, args.file)
    session.save()
    _print_import(result)
    return 0


# Reports


def cmd_due(args, clock):
    session = Session(args)
    vehicle_id = normalise_vehicle_id(args.vehicle) if args.vehicle else None
    rows = due_rows(session.fleet, _day(args.as_of, clock), vehicle_id)
    print(render("due", rows, args.format), end="")
    return 0


def cmd_remind(args, clock):
    session = Session(args)
    for reminder in reminders(session.fleet, _day(args.as_of, clock)):
        print(reminder.text)
    return 0


def cmd_costs(args, clock):
    session = Session(args)
    print(render("costs", cost_rows(session.fleet, _period(args)), args.format), end="")
    return 0


def cmd_spend(args, clock):
    session = Session(args)
    print(render("spend", spend_rows(session.fleet, _period(args)), args.format), end="")
    return 0


def cmd_check(args, clock):
    session = Session(args)
    findings = run_checks(session.fleet, _day(args.as_of, clock))
    for finding in findings:
        print(f"{finding.subject}: {finding.text}")
    if not findings:
        print("nothing to report")
    return 0


def cmd_downtime(args, clock):
    session = Session(args)
    print(render("downtime", downtime_rows(session.fleet, _period(args)), args.format), end="")
    return 0
