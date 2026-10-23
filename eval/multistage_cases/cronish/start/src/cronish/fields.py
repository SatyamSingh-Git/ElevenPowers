"""The five fields of a schedule expression and how each one is read."""
from dataclasses import dataclass, field

from ._generated import DAY_NAMES, MONTH_NAMES
from .errors import ScheduleError


@dataclass(frozen=True)
class FieldSpec:
    name: str
    low: int
    high: int
    names: dict = field(default_factory=dict)

    @property
    def size(self):
        return self.high - self.low + 1


MINUTE = FieldSpec("minute", 0, 59)
HOUR = FieldSpec("hour", 0, 23)
DAY = FieldSpec("day", 1, 31)
MONTH = FieldSpec("month", 1, 12, {name: number for number, name in enumerate(MONTH_NAMES, 1)})
WEEKDAY = FieldSpec("weekday", 0, 6, {name: number for number, name in enumerate(DAY_NAMES)})

FIELDS = (MINUTE, HOUR, DAY, MONTH, WEEKDAY)


def parse_field(text, spec):
    """The sorted values one field selects, e.g. ``"*/20"`` -> ``(0, 20, 40)``."""
    values = set()
    for part in text.split(","):
        values.update(_expand(part, spec))
    return tuple(sorted(values))


def _expand(part, spec):
    body, slash, step_text = part.partition("/")
    step = 1
    if slash:
        if not step_text.isdigit():
            raise ScheduleError(spec.name, f"cannot parse '{part}'")
        step = int(step_text)
    if body == "*":
        low, high = spec.low, spec.high
    elif "-" in body:
        first, _, last = body.partition("-")
        low, high = _value(first, spec), _value(last, spec)
        if low > high:
            raise ScheduleError(spec.name, f"range {body} runs backwards")
    else:
        low = _value(body, spec)
        # "5/15" starts at 5 and steps to the end of the field, as in Vixie cron.
        high = spec.high if slash else low
    return range(low, high + 1, step)


def _value(text, spec):
    if text.isdigit():
        number = int(text)
    elif text.isalpha():
        if text.lower() not in spec.names:
            raise ScheduleError(spec.name, f"unknown name '{text}'")
        number = spec.names[text.lower()]
    else:
        raise ScheduleError(spec.name, f"cannot parse '{text}'")
    if not spec.low <= number <= spec.high:
        raise ScheduleError(spec.name, f"value {number} out of range {spec.low}-{spec.high}")
    return number
