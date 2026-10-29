"""One-line descriptions of logged alerts, as the commands and the daily report print them."""
from ..core.units import format_value
from .formatting import label

MESSAGES = {
    "high": "{zone} {kind} at {value} {unit} is above {limit} {unit}",
    "low": "{zone} {kind} at {value} {unit} is below {limit} {unit}",
    "stale": "{zone} sensor {sensor} has not reported for {limit} minutes",
}


def describe(record):
    """Describe one alerts log record."""
    template = MESSAGES[record["code"]]
    kind = record["kind"]
    if record["code"] == "stale":
        limit = f"{record['limit']:g}"
    else:
        limit = format_value(kind, record["limit"])
    return template.format(
        zone=record["zone"],
        sensor=record["sensor"],
        kind=label(kind),
        value=format_value(kind, record["value"]),
        unit=record["unit"],
        limit=limit,
    )


def timed(record):
    """The description prefixed with the time of day the alert was raised."""
    return f"{record['at'][11:16]} {describe(record)}"
