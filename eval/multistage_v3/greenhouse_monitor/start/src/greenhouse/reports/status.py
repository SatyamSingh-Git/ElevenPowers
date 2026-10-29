"""The status table: each sensor's latest reading and whether it has gone quiet."""
import json
from datetime import timedelta

from ..core.clock import format_timestamp
from .formatting import number, table


def status_rows(latest, stale_minutes, now):
    """One row per sensor, sorted by sensor id."""
    quiet_after = timedelta(minutes=stale_minutes)
    rows = []
    for sensor in sorted(latest):
        reading = latest[sensor]
        rows.append({
            "sensor": sensor,
            "zone": reading.zone,
            "kind": reading.kind,
            "value": reading.value,
            "unit": reading.unit,
            "at": format_timestamp(reading.at),
            "stale": now - reading.at > quiet_after,
        })
    return rows


def render_status(rows, fmt):
    if fmt == "json":
        return json.dumps(rows, indent=2)
    if not rows:
        return "no readings yet"
    quiet = sum(1 for r in rows if r["stale"])
    return f"{len(rows)} sensors, {quiet} stale\n" + table(
        ["sensor", "zone", "kind", "value", "unit", "last reading", ""],
        [
            [r["sensor"], r["zone"], r["kind"], number(r["kind"], r["value"]), r["unit"], r["at"],
             "STALE" if r["stale"] else ""]
            for r in rows
        ],
    )
