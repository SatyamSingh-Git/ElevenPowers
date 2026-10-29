"""The daily report: the day's statistics, light and climate, alerts and the irrigation outlook."""
from dataclasses import dataclass, field
from datetime import date

from .environment import climate_text, light_text
from .export import summary_text
from .formatting import heading, label, signed
from .messages import timed


@dataclass
class DayView:
    """Everything the daily report shows about one day.

    ``alerts`` are alerts log records; ``changes`` maps (zone, kind) to how
    far the mean moved since the day before.
    """

    day: date
    stats: list
    alerts: list
    suggestions: list
    changes: dict = field(default_factory=dict)
    lights: list = field(default_factory=list)
    climate: list = field(default_factory=list)
    target_dli: float = 0.0


def daily_report(view):
    parts = [
        heading(f"Greenhouse report {view.day.isoformat()}"),
        summary_text(view.day, view.stats),
        _changes_section(view.stats, view.changes),
        light_text(view.lights, view.target_dli),
        climate_text(view.climate),
        _alerts_section(view.alerts),
        _irrigation_section(view.suggestions),
    ]
    return "\n\n".join(part for part in parts if part)


def _changes_section(stats, changes):
    lines = [
        f"  {s.zone} {label(s.kind)} {signed(s.kind, changes[(s.zone, s.kind)])} {s.unit}"
        for s in stats
        if (s.zone, s.kind) in changes
    ]
    return "\n".join(["Change since the day before:", *lines]) if lines else ""


def _alerts_section(records):
    if not records:
        return "Alerts: none"
    return "\n".join([f"Alerts: {len(records)}", *(f"  {timed(record)}" for record in records)])


def _irrigation_section(suggestions):
    if not suggestions:
        return "Irrigation: no zone has a moisture target"
    watered = [s for s in suggestions if s.minutes > 0]
    lines = [f"Irrigation: {len(watered)} of {len(suggestions)} zones need water"]
    lines += [f"  {s.zone}: {s.minutes} min ({s.reason})" for s in suggestions]
    return "\n".join(lines)
