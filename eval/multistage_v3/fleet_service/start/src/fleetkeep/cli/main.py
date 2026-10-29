"""Argument parsing and dispatch for `fleetkeep`."""
import argparse
import sys

from ..clock import SystemClock
from ..errors import FleetError
from ..model.inspection import SEVERITIES, TYRE_POSITIONS
from ..model.vehicle import VEHICLE_CLASSES
from ..reports.render import RENDERERS
from . import commands


def _format_option(parser):
    parser.add_argument("--format", choices=list(RENDERERS),
                        default="table", help="output format (default: table)")


def _period_options(parser):
    parser.add_argument("--from", dest="start", required=True, help="first day, YYYY-MM-DD")
    parser.add_argument("--to", dest="end", required=True, help="last day, YYYY-MM-DD")


def _add(subparsers, name, handler, help_text):
    parser = subparsers.add_parser(name, help=help_text)
    parser.set_defaults(handler=handler)
    return parser


def build_parser():
    parser = argparse.ArgumentParser(prog="fleetkeep", description="Fleet maintenance records.")
    parser.add_argument("--fleet", default=".", help="fleet directory (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    init = _add(sub, "init", commands.cmd_init, "create a fleet directory")
    init.add_argument("--name", required=True)

    vehicle = sub.add_parser("vehicle", help="manage vehicles").add_subparsers(
        dest="action", required=True)
    add = _add(vehicle, "add", commands.cmd_vehicle_add, "add a vehicle")
    add.add_argument("id")
    add.add_argument("--class", dest="vehicle_class", required=True, choices=VEHICLE_CLASSES)
    add.add_argument("--make", required=True)
    add.add_argument("--model", required=True)
    add.add_argument("--year", type=int, required=True)
    add.add_argument("--in-service", required=True, help="YYYY-MM-DD")
    add.add_argument("--odometer", default="0", help="odometer when it joined the fleet")
    _add(vehicle, "import", commands.cmd_vehicle_import,
         "import a delivery schedule").add_argument("file")
    retire = _add(vehicle, "retire", commands.cmd_vehicle_retire, "take a vehicle out of the fleet")
    retire.add_argument("id")
    retire.add_argument("--on")
    show_vehicle = _add(vehicle, "show", commands.cmd_vehicle_show, "one vehicle at a glance")
    show_vehicle.add_argument("id")
    show_vehicle.add_argument("--as-of")

    vehicles = _add(sub, "vehicles", commands.cmd_vehicles, "list vehicles")
    vehicles.add_argument("--as-of")
    _format_option(vehicles)

    catalog = _add(sub, "catalog", commands.cmd_catalog, "list the service catalog")
    catalog.add_argument("--class", dest="vehicle_class", choices=VEHICLE_CLASSES)
    _format_option(catalog)

    odometer = sub.add_parser("odometer", help="odometer readings").add_subparsers(
        dest="action", required=True)
    reading = _add(odometer, "add", commands.cmd_odometer_add, "record a reading")
    reading.add_argument("id")
    reading.add_argument("value")
    reading.add_argument("--on")
    fix = _add(odometer, "fix", commands.cmd_odometer_fix, "correct a mistyped reading")
    fix.add_argument("id")
    fix.add_argument("value")
    fix.add_argument("--on", required=True, help="day of the reading to correct")
    _add(odometer, "import", commands.cmd_odometer_import,
         "import telematics reports").add_argument("file")
    _add(odometer, "list", commands.cmd_odometer_list, "a vehicle's readings").add_argument("id")

    fuel = sub.add_parser("fuel", help="fill-ups").add_subparsers(dest="action", required=True)
    fill = _add(fuel, "add", commands.cmd_fuel_add, "record a fill-up")
    fill.add_argument("id")
    fill.add_argument("--gallons", required=True)
    fill.add_argument("--cost", required=True)
    fill.add_argument("--odometer")
    fill.add_argument("--on")
    _add(fuel, "import", commands.cmd_fuel_import, "import a fuel-card export").add_argument("file")
    card = _add(fuel, "card", commands.cmd_fuel_card, "assign a fuel card to a vehicle")
    card.add_argument("card")
    card.add_argument("id")
    _add(fuel, "list", commands.cmd_fuel_list, "a vehicle's fill-ups").add_argument("id")
    fuel_report = _add(fuel, "report", commands.cmd_fuel_report, "fuel bought and economy")
    _period_options(fuel_report)
    _format_option(fuel_report)

    history = sub.add_parser("history", help="service history").add_subparsers(
        dest="action", required=True)
    _add(history, "import", commands.cmd_history_import, "import old service history").add_argument("file")
    history_show = _add(history, "show", commands.cmd_history_show, "a vehicle's service history")
    history_show.add_argument("id")
    _format_option(history_show)

    wo = sub.add_parser("wo", help="work orders").add_subparsers(dest="action", required=True)
    wo_open = _add(wo, "open", commands.cmd_wo_open, "open a work order")
    wo_open.add_argument("id")
    wo_open.add_argument("--service", action="append", default=[], help="service code, repeatable")
    wo_open.add_argument("--note", default="")
    wo_open.add_argument("--breakdown", action="store_true", help="unplanned: the vehicle broke down")
    wo_open.add_argument("--defect", action="append", default=[], help="defect it fixes, repeatable")
    wo_open.add_argument("--on")
    _add(wo, "cancel", commands.cmd_wo_cancel, "cancel an order opened by mistake").add_argument("order")
    part = _add(wo, "part", commands.cmd_wo_part, "charge a part")
    part.add_argument("order")
    part.add_argument("--number", required=True)
    part.add_argument("--description", default="")
    part.add_argument("--qty", type=int, default=1)
    part.add_argument("--price", help="unit price (default: average cost of a stocked part)")
    labour = _add(wo, "labour", commands.cmd_wo_labour, "charge labour")
    labour.add_argument("order")
    labour.add_argument("--mechanic", required=True)
    labour.add_argument("--hours", required=True)
    labour.add_argument("--rate", help="hourly rate (default: the fleet's labour rate)")
    close = _add(wo, "close", commands.cmd_wo_close, "close a work order")
    close.add_argument("order")
    close.add_argument("--on")
    close.add_argument("--odometer")
    show = _add(wo, "show", commands.cmd_wo_show, "show a work order")
    show.add_argument("order")
    show.add_argument("--json", action="store_true")
    wo_list = _add(wo, "list", commands.cmd_wo_list, "list work orders")
    wo_list.add_argument("--open", action="store_true")
    wo_list.add_argument("--vehicle")
    _format_option(wo_list)

    parts = sub.add_parser("parts", help="parts stock").add_subparsers(dest="action", required=True)
    receive = _add(parts, "receive", commands.cmd_parts_receive, "receive parts into stock")
    receive.add_argument("number")
    receive.add_argument("--qty", type=int, required=True)
    receive.add_argument("--cost", required=True, help="unit cost")
    receive.add_argument("--description", default="")
    count = _add(parts, "count", commands.cmd_parts_count, "record a stock count")
    count.add_argument("number")
    count.add_argument("on_hand", type=int)
    _format_option(_add(parts, "stock", commands.cmd_parts_stock, "parts on hand"))

    defect = sub.add_parser("defect", help="inspection defects").add_subparsers(
        dest="action", required=True)
    report = _add(defect, "report", commands.cmd_defect_report, "record a defect")
    report.add_argument("id")
    report.add_argument("--description", required=True)
    report.add_argument("--severity", choices=SEVERITIES, default="minor")
    report.add_argument("--on")
    defect_list = _add(defect, "list", commands.cmd_defect_list, "list defects")
    defect_list.add_argument("--open", action="store_true")
    defect_list.add_argument("--vehicle")
    _format_option(defect_list)

    tyre = sub.add_parser("tyre", help="tyre tread").add_subparsers(dest="action", required=True)
    tread = _add(tyre, "add", commands.cmd_tyre_add, "record a tread depth")
    tread.add_argument("id")
    tread.add_argument("position", type=str.upper, choices=TYRE_POSITIONS)
    tread.add_argument("depth", type=int, help="32nds of an inch")
    tread.add_argument("--on")
    tyre_list = _add(tyre, "list", commands.cmd_tyre_list, "latest tread at each position")
    tyre_list.add_argument("id")
    tyre_list.add_argument("--as-of")

    timesheet = sub.add_parser("timesheet", help="mechanics' timesheets").add_subparsers(
        dest="action", required=True)
    _add(timesheet, "import", commands.cmd_timesheet_import, "charge a timesheet").add_argument("file")

    due = _add(sub, "due", commands.cmd_due, "services due")
    due.add_argument("--as-of")
    due.add_argument("--vehicle")
    _format_option(due)

    _add(sub, "remind", commands.cmd_remind, "reminders for the workshop").add_argument("--as-of")

    costs = _add(sub, "costs", commands.cmd_costs, "running costs and cost per mile")
    _period_options(costs)
    _format_option(costs)

    spend = _add(sub, "spend", commands.cmd_spend, "spending by month")
    _period_options(spend)
    _format_option(spend)

    _add(sub, "check", commands.cmd_check, "look for forgotten records").add_argument("--as-of")

    downtime = _add(sub, "downtime", commands.cmd_downtime, "shop days and availability")
    _period_options(downtime)
    _format_option(downtime)

    summary = _add(sub, "summary", commands.cmd_summary, "each vehicle's period at a glance")
    _period_options(summary)
    _format_option(summary)
    return parser


def main(argv=None, clock=None):
    """Run one command and return its exit status."""
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args, clock or SystemClock())
    except FleetError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def run():
    sys.exit(main())
