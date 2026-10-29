"""Renderers for the daily summary, looked up by format name."""
import csv
import io
import json

from ..core.errors import ValidationError
from .formatting import heading, number, table

RENDERERS = {}


def renderer(name):
    def register(function):
        RENDERERS[name] = function
        return function

    return register


def render_summary(name, day, stats):
    try:
        render = RENDERERS[name]
    except KeyError:
        raise ValidationError(f"unknown format: {name}") from None
    return render(day, stats)


def summary_record(stats):
    return {
        "zone": stats.zone,
        "kind": stats.kind,
        "unit": stats.unit,
        "count": stats.count,
        "min": stats.low,
        "max": stats.high,
        "mean": stats.mean,
    }


@renderer("text")
def summary_text(day, stats):
    title = heading(f"Summary for {day.isoformat()}")
    if not stats:
        return f"{title}\nno readings"
    rows = [
        [s.zone, s.kind, s.count, number(s.kind, s.low), number(s.kind, s.high), number(s.kind, s.mean), s.unit]
        for s in stats
    ]
    return f"{title}\n" + table(["zone", "kind", "count", "min", "max", "mean", "unit"], rows)


@renderer("csv")
def summary_csv(day, stats):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "zone", "kind", "unit", "count", "min", "max", "mean"])
    for s in stats:
        writer.writerow([day.isoformat(), s.zone, s.kind, s.unit, s.count,
                         number(s.kind, s.low), number(s.kind, s.high), number(s.kind, s.mean)])
    return buffer.getvalue().rstrip("\n")


@renderer("json")
def summary_json(day, stats):
    return json.dumps({"date": day.isoformat(), "rows": [summary_record(s) for s in stats]}, indent=2)
