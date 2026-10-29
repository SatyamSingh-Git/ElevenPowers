"""Handlers for the read-only views: light, climate, trends, sensors and configuration.

None of them writes anything except ``digest``, which leaves a file in the outbox.
"""
from dataclasses import fields
from datetime import timedelta

from ..config.thresholds import load_thresholds
from ..core.clock import parse_day
from ..core.errors import ValidationError
from ..core.units import check_kind, kinds
from ..reports.charts import day_chart
from ..reports.digest import alert_counts, counts_text, digest_text, write_digest
from ..reports.environment import (
    climate_text,
    condensation_text,
    degree_days_text,
    light_text,
    sensors_text,
    uptime_text,
)
from ..reports.formatting import number, table
from ..reports.readings_export import export_readings
from ..reports.weekly import week_days, weekly_table
from ..services.climate import zone_climate
from ..services.condensation import risk_hours
from ..services.degree_days import season_degree_days
from ..services.inventory import inventory, moved
from ..services.irrigation import suggest, zone_moisture
from ..services.light import daily_light
from ..services.summary import hourly_means, summarize
from ..services.trends import trends
from ..services.uptime import find_gaps, uptime
from ..services.water import estimate, per_square_metre
from ..storage.alerts_log import read_alerts
from ..storage.calibration import load_calibration
from ..storage.history import latest_by_sensor, load_readings


def cmd_light(args, context):
    settings = context.settings()
    readings = load_readings(context.data.readings, day=context.day(args.date))
    context.say(light_text(daily_light(readings, settings), settings.target_dli))
    return 0


def cmd_climate(args, context):
    settings = context.settings()
    stats = summarize(load_readings(context.data.readings, day=context.day(args.date)))
    context.say(climate_text(zone_climate(stats, settings)))
    return 0


def cmd_weekly(args, context):
    last_day = context.day(args.date)
    days = set(week_days(last_day))
    by_day = {}
    for reading in load_readings(context.data.readings):
        if reading.at.date() in days:
            by_day.setdefault(reading.at.date(), []).append(reading)
    context.say(weekly_table(last_day, {day: summarize(items) for day, items in by_day.items()}))
    return 0


def cmd_chart(args, context):
    day = context.day(args.date)
    hourly = hourly_means(load_readings(context.data.readings, day=day, zone=args.zone))
    line = day_chart(hourly, args.zone, check_kind(args.kind))
    context.say(line if line is not None else f"no {args.kind} readings for {args.zone} on {day.isoformat()}")
    return 0


def cmd_condensation(args, context):
    readings = load_readings(context.data.readings, day=context.day(args.date))
    context.say(condensation_text(risk_hours(readings, context.settings().condensation_margin)))
    return 0


def cmd_gdd(args, context):
    last = context.day(args.date)
    first = parse_day(args.since)
    if first > last:
        raise ValidationError(f"--since {first.isoformat()} is after {last.isoformat()}")
    days = [first + timedelta(days=n) for n in range((last - first).days + 1)]
    by_day = {}
    for reading in load_readings(context.data.readings):
        if first <= reading.at.date() <= last:
            by_day.setdefault(reading.at.date(), []).append(reading)
    stats = {day: summarize(items) for day, items in by_day.items()}
    context.say(degree_days_text(season_degree_days(context.layout(), stats, days), first, last))
    return 0


def cmd_export(args, context):
    first, last = parse_day(args.start), parse_day(args.end)
    readings = [
        reading
        for reading in load_readings(context.data.readings, zone=args.zone)
        if first <= reading.at.date() <= last
    ]
    context.say(export_readings(args.format, readings))
    return 0


def cmd_trend(args, context):
    found = trends(load_readings(context.data.readings), context.clock.now(), args.hours)
    if not found:
        context.say(f"not enough readings in the last {args.hours} hours")
    for trend in found:
        context.say(f"{trend.sensor} {trend.zone} {trend.kind} {trend.direction} "
                    f"{trend.per_hour:+.2f} {trend.unit}/h ({trend.points} readings)")
    return 0


def cmd_water(args, context):
    layout = context.layout()
    latest = latest_by_sensor(load_readings(context.data.readings))
    water = estimate(layout, suggest(layout, latest, context.settings()))
    spread = per_square_metre(layout, water)
    for zone, litres in water.litres.items():
        per_m2 = f", {spread[zone]:.2f} l/m2" if zone in spread else ""
        context.say(f"{zone}: {litres:.1f} l{per_m2}")
    if water.unknown:
        context.say(f"no flow_lpm for {', '.join(water.unknown)}")
    context.say(f"total {water.total:.1f} l")
    return 0


def cmd_digest(args, context):
    day = context.day(args.date)
    text = digest_text(day, read_alerts(context.data.alerts, day=day))
    target = write_digest(context.data.outbox, day, text)
    context.say(f"wrote {target.name}")
    return 0


def cmd_alert_stats(args, context):
    last = context.day(args.date)
    first = last - timedelta(days=args.days - 1)
    records = [
        record
        for record in read_alerts(context.data.alerts)
        if first.isoformat() <= record["at"][:10] <= last.isoformat()
    ]
    context.say(counts_text(alert_counts(records), first, last))
    return 0


def cmd_sensors(args, context):
    readings = load_readings(context.data.readings)
    context.say(sensors_text(inventory(readings), moved(readings)))
    return 0


def cmd_uptime(args, context):
    day = context.day(args.date)
    now = context.clock.now()
    readings = load_readings(context.data.readings, day=day)
    gaps = find_gaps(readings, day, context.settings().gap_minutes, now)
    shares = uptime(gaps, {reading.sensor for reading in readings}, day, now)
    context.say(uptime_text(gaps, shares))
    return 0


def cmd_zones(args, context):
    latest = latest_by_sensor(load_readings(context.data.readings))
    rows = []
    for zone in context.layout().zones():
        moisture = zone_moisture(latest, zone.id)
        rows.append([
            zone.id,
            zone.name,
            zone.crop,
            zone.valve,
            "-" if zone.target_moisture is None else f"{zone.target_moisture:.1f}",
            "-" if moisture is None else f"{moisture:.1f}",
        ])
    context.say(table(["zone", "name", "crop", "valve", "target %", "moisture %"], rows))
    return 0


def cmd_limits(args, context):
    layout, thresholds = context.layout(), load_thresholds(context.data.thresholds)
    rows = []
    for zone in layout.ids():
        for kind in kinds():
            limits = thresholds.limits(zone, kind)
            if not limits.is_empty():
                rows.append([zone, kind, number(kind, limits.low), number(kind, limits.high)])
    context.say(table(["zone", "kind", "low", "high"], rows) if rows else "no limits set")
    return 0


def cmd_offsets(args, context):
    offsets = load_calibration(context.data.calibration).items()
    if not offsets:
        context.say("no calibration offsets")
    else:
        context.say(table(["sensor", "offset"], [[sensor, f"{offset:+.2f}"] for sensor, offset in offsets]))
    return 0


def cmd_settings(args, context):
    settings = context.settings()
    rows = [[item.name, getattr(settings, item.name)] for item in fields(settings)]
    context.say(table(["setting", "value"], rows))
    return 0


VIEWS = {
    "light": cmd_light,
    "climate": cmd_climate,
    "weekly": cmd_weekly,
    "chart": cmd_chart,
    "condensation": cmd_condensation,
    "gdd": cmd_gdd,
    "export": cmd_export,
    "trend": cmd_trend,
    "water": cmd_water,
    "digest": cmd_digest,
    "alert-stats": cmd_alert_stats,
    "sensors": cmd_sensors,
    "uptime": cmd_uptime,
    "zones": cmd_zones,
    "limits": cmd_limits,
    "offsets": cmd_offsets,
    "settings": cmd_settings,
}
