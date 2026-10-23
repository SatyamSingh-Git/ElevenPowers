"""Schedule expressions: five fields, or one of the named shortcuts."""
from dataclasses import dataclass

from .errors import ScheduleError
from .fields import FIELDS, parse_field

SHORTCUTS = {
    "@yearly": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@hourly": "0 * * * *",
}


@dataclass(frozen=True)
class Schedule:
    minutes: tuple
    hours: tuple
    days: tuple
    months: tuple
    weekdays: tuple
    day_star: bool
    weekday_star: bool
    expression: str

    def __str__(self):
        return self.expression


def expand(text):
    """The five field texts of an expression, with any shortcut resolved."""
    expression = " ".join(text.split())
    if expression.startswith("@"):
        if expression.lower() not in SHORTCUTS:
            raise ScheduleError("expression", f"unknown shortcut '{expression}'")
        expression = SHORTCUTS[expression.lower()]
    parts = expression.split()
    if len(parts) != len(FIELDS):
        raise ScheduleError("expression", f"expected {len(FIELDS)} fields, got {len(parts)}")
    return parts


def parse(text):
    parts = expand(text)
    values = [parse_field(part, spec) for part, spec in zip(parts, FIELDS)]
    return Schedule(
        *values,
        day_star=parts[2].startswith("*"),
        weekday_star=parts[4].startswith("*"),
        expression=" ".join(text.split()),
    )
