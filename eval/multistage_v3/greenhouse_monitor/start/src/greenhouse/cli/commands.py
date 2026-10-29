"""Handlers for the commands that import readings, keep the logs and drive irrigation.

Each takes the parsed arguments and a Context and returns an exit code.
"""
import sys
from datetime import timedelta

from ..config.consistency import problems
from ..config.thresholds import load_thresholds
from ..core.clock import parse_time_of_day
from ..core.errors import ValidationError
from ..core.units import format_value
from ..reports.daily import DayView, daily_report
from ..reports.export import render_summary
from ..reports.messages import describe, timed
from ..reports.status import render_status, status_rows
from ..services.alerts import evaluate, unreported
from ..services.climate import zone_climate
from ..services.ingest import ingest_file
from ..services.irrigation import suggest, total_minutes
from ..services.light import daily_light
from ..services.manual import record_manual
from ..services.summary import mean_changes, summarize
from ..services.valves import build_schedule, planned_minutes, write_schedule
from ..storage.alerts_log import alert_record, append_alerts, logged_keys, read_alerts
from ..storage.archive import archive_readings
from ..storage.calibration import load_calibration
from ..storage.history import latest_by_sensor, load_readings
from ..storage.plans import write_plan
from ..storage.readings_log import ReadingsLog


def cmd_ingest(args, context):
    log = ReadingsLog(context.data.readings)
    layout = context.layout()
    calibration = load_calibration(context.data.calibration)
    imported = rejected = 0
    for name in args.files:
        result = ingest_file(name, log, layout, calibration)
        for problem in result.problems:
            print(f"{name}: {problem}" if len(args.files) > 1 else problem, file=sys.stderr)
        imported += result.imported
        rejected += result.rejected
    context.say(f"imported {imported} rows, rejected {rejected}")
    return 0


def cmd_record(args, context):
    reading = record_manual(
        ReadingsLog(context.data.readings),
        context.layout(),
        load_calibration(context.data.calibration),
        zone=args.zone,
        sensor=args.sensor,
        kind=args.kind,
        value=args.value,
        unit=args.unit,
        at=context.clock.now(),
    )
    value = format_value(reading.kind, reading.value)
    context.say(f"recorded {reading.sensor} {reading.kind} {value} {reading.unit}")
    return 0


def cmd_calibrate(args, context):
    store = load_calibration(context.data.calibration)
    if args.clear:
        if not store.clear(args.sensor):
            raise ValidationError(f"no offset for {args.sensor}")
        store.save()
        context.say(f"cleared {args.sensor}")
    elif args.offset is None:
        context.say(f"{args.sensor}: {store.offset_for(args.sensor):+.2f}")
    else:
        store.set_offset(args.sensor, args.offset, context.settings().max_offset)
        store.save()
        context.say(f"calibrated {args.sensor}: {args.offset:+.2f}")
    return 0


def cmd_summary(args, context):
    day = context.day(args.date)
    stats = summarize(load_readings(context.data.readings, day=day))
    context.say(render_summary(args.format or context.settings().report_format, day, stats))
    return 0


def cmd_check(args, context):
    now = context.clock.now()
    latest = latest_by_sensor(load_readings(context.data.readings))
    alerts = evaluate(latest, load_thresholds(context.data.thresholds), context.settings(), now)
    fresh = unreported(alerts, logged_keys(read_alerts(context.data.alerts, day=now.date())))
    if not args.dry_run:
        append_alerts(context.data.alerts, fresh)
    for alert in fresh:
        context.say(describe(alert_record(alert)))
    context.say(f"{len(fresh)} new alerts")
    return 0


def cmd_alerts(args, context):
    day = context.day(args.date)
    records = read_alerts(context.data.alerts, day=day)
    if not records:
        context.say(f"no alerts on {day.isoformat()}")
    for record in records:
        context.say(timed(record))
    return 0


def cmd_status(args, context):
    latest = latest_by_sensor(load_readings(context.data.readings))
    rows = status_rows(latest, context.settings().stale_minutes, context.clock.now())
    context.say(render_status(rows, args.format))
    return 0


def cmd_irrigate(args, context):
    latest = latest_by_sensor(load_readings(context.data.readings))
    suggestions = suggest(context.layout(), latest, context.settings())
    write_plan(context.data.plan, suggestions)
    for suggestion in suggestions:
        context.say(f"{suggestion.zone}: {suggestion.minutes} min ({suggestion.reason})")
    context.say(f"total {total_minutes(suggestions)} min")
    return 0


def cmd_schedule(args, context):
    start = parse_time_of_day(args.start)
    lines = build_schedule(planned_minutes(context.data.plan), context.layout(), start)
    write_schedule(context.data.valves, lines)
    for line in lines:
        context.say(line)
    context.say(f"scheduled {len(lines)} valves")
    return 0


def cmd_report(args, context):
    settings = context.settings()
    day = context.day(args.date)
    readings = load_readings(context.data.readings, day=day)
    stats = summarize(readings)
    previous = summarize(load_readings(context.data.readings, day=day - timedelta(days=1)))
    view = DayView(
        day=day,
        stats=stats,
        alerts=read_alerts(context.data.alerts, day=day),
        suggestions=suggest(context.layout(), latest_by_sensor(readings), settings),
        changes=mean_changes(stats, previous),
        lights=daily_light(readings, settings),
        climate=zone_climate(stats, settings),
        target_dli=settings.target_dli,
    )
    context.say(daily_report(view))
    return 0


def cmd_archive(args, context):
    days = args.days if args.days is not None else context.settings().archive_after_days
    cutoff = context.clock.now().date() - timedelta(days=days)
    moved_rows = archive_readings(context.data.readings, context.data.archive, cutoff)
    for month, count in moved_rows.items():
        context.say(f"archived {count} rows to readings-{month}.csv")
    context.say(f"archived {sum(moved_rows.values())} rows from before {cutoff.isoformat()}")
    return 0


def cmd_validate(args, context):
    found = problems(
        context.layout(),
        load_thresholds(context.data.thresholds),
        load_calibration(context.data.calibration).items(),
        context.settings(),
    )
    for problem in found:
        context.say(problem)
    context.say("configuration ok" if not found else f"{len(found)} problems")
    return 1 if found else 0


COMMANDS = {
    "ingest": cmd_ingest,
    "record": cmd_record,
    "calibrate": cmd_calibrate,
    "summary": cmd_summary,
    "check": cmd_check,
    "alerts": cmd_alerts,
    "status": cmd_status,
    "irrigate": cmd_irrigate,
    "schedule": cmd_schedule,
    "report": cmd_report,
    "archive": cmd_archive,
    "validate": cmd_validate,
}
