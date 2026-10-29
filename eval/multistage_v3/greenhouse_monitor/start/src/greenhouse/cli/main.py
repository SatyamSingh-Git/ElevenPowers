"""Entry point: ``greenhouse [--data DIR] --now YYYY-MM-DDTHH:MM:SS COMMAND``.

The scheduler that runs the commands passes ``--now``; there is no default,
so re-running an old day gives the same answer it gave then.
"""
import argparse
import sys

from ..core.clock import FixedClock, parse_timestamp
from ..core.errors import GreenhouseError
from ..storage.paths import DataDir
from .commands import COMMANDS
from .context import Context
from .views import VIEWS

HANDLERS = {**COMMANDS, **VIEWS}


def build_parser():
    parser = argparse.ArgumentParser(prog="greenhouse", description="Greenhouse monitoring.")
    parser.add_argument("--data", default=".", help="data directory (default: the current directory)")
    parser.add_argument("--now", help="the time the command runs at, YYYY-MM-DDTHH:MM:SS")
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    ingest = commands.add_parser("ingest", help="import controller exports")
    ingest.add_argument("files", nargs="+", metavar="FILE",
                        help="CSV export with time,zone,sensor,kind,value,unit")

    record = commands.add_parser("record", help="log a reading taken with a hand-held meter")
    record.add_argument("sensor")
    record.add_argument("kind")
    record.add_argument("value", type=float)
    record.add_argument("unit")
    record.add_argument("--zone", required=True)

    calibrate = commands.add_parser("calibrate", help="show, set or clear a sensor's offset")
    calibrate.add_argument("sensor")
    calibrate.add_argument("offset", type=float, nargs="?", help="offset in the kind's canonical unit")
    calibrate.add_argument("--clear", action="store_true", help="remove the sensor's offset")

    summary = commands.add_parser("summary", help="daily statistics per zone and kind")
    summary.add_argument("--date", help="YYYY-MM-DD (default: today)")
    summary.add_argument("--format", help="text, csv or json (default: the report_format setting)")

    check = commands.add_parser("check", help="check latest readings and log new alerts")
    check.add_argument("--dry-run", action="store_true", help="print new alerts without logging them")

    alerts = commands.add_parser("alerts", help="list the alerts logged on a day")
    alerts.add_argument("--date", help="YYYY-MM-DD (default: today)")

    status = commands.add_parser("status", help="each sensor's latest reading")
    status.add_argument("--format", choices=("text", "json"), default="text")

    commands.add_parser("irrigate", help="suggest irrigation and write the plan")

    schedule = commands.add_parser("schedule", help="turn the irrigation plan into a valve schedule")
    schedule.add_argument("--start", default="06:00", help="HH:MM the first valve opens (default: 06:00)")

    report = commands.add_parser("report", help="the daily report")
    report.add_argument("--date", help="YYYY-MM-DD (default: today)")

    for name, text in (("light", "daily light integral and photoperiod per zone"),
                       ("climate", "vapour pressure deficit and dew point per zone"),
                       ("condensation", "hours when the air came close to its dew point"),
                       ("weekly", "daily means over the week ending on a day"),
                       ("uptime", "reporting gaps and uptime per sensor")):
        view = commands.add_parser(name, help=text)
        view.add_argument("--date", help="YYYY-MM-DD (default: today)")

    gdd = commands.add_parser("gdd", help="growing degree days per zone since a day")
    gdd.add_argument("--since", required=True, help="first day, YYYY-MM-DD")
    gdd.add_argument("--date", help="last day, YYYY-MM-DD (default: today)")

    export = commands.add_parser("export", help="readings over a range of days")
    export.add_argument("start", help="first day, YYYY-MM-DD")
    export.add_argument("end", help="last day, YYYY-MM-DD")
    export.add_argument("--format", choices=("csv", "json"), default="csv")
    export.add_argument("--zone", help="only this zone")

    chart = commands.add_parser("chart", help="hourly sparkline of one zone and kind")
    chart.add_argument("zone")
    chart.add_argument("kind")
    chart.add_argument("--date", help="YYYY-MM-DD (default: today)")

    trend = commands.add_parser("trend", help="how fast each sensor's value is moving")
    trend.add_argument("--hours", type=int, default=3, help="window before now (default: 3)")

    commands.add_parser("water", help="litres the current irrigation suggestions would use")

    digest = commands.add_parser("digest", help="write the day's alert digest to the outbox")
    digest.add_argument("--date", help="YYYY-MM-DD (default: today)")

    alert_stats = commands.add_parser("alert-stats", help="alert counts per zone and code")
    alert_stats.add_argument("--days", type=int, default=7, help="days ending on --date (default: 7)")
    alert_stats.add_argument("--date", help="last day, YYYY-MM-DD (default: today)")

    commands.add_parser("sensors", help="every sensor seen and how often it reports")

    archive = commands.add_parser("archive", help="move old readings into monthly archive files")
    archive.add_argument("--days", type=int, help="keep this many days (default: the archive_after_days setting)")

    commands.add_parser("zones", help="the zones, their targets and current soil moisture")
    commands.add_parser("limits", help="the alert limits in force per zone and kind")
    commands.add_parser("offsets", help="every sensor's calibration offset")
    commands.add_parser("settings", help="the settings in force, defaults included")
    commands.add_parser("validate", help="cross-check the configuration files")
    return parser


def main(argv=None, clock=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if clock is None:
        if args.now is None:
            parser.error("--now is required")
        try:
            clock = FixedClock(parse_timestamp(args.now))
        except GreenhouseError as error:
            parser.error(str(error))
    context = Context(data=DataDir(args.data), clock=clock, out=sys.stdout)
    try:
        return HANDLERS[args.command](args, context)
    except GreenhouseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def run():
    sys.exit(main())
