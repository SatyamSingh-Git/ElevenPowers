"""One row of hours: who, which day, how many hours and of what kind."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

KINDS = ("work", "sick")
DEFAULT_KIND = "work"
HUNDREDTH = Decimal("0.01")


@dataclass(frozen=True)
class TimesheetEntry:
    employee_id: str
    day: date
    hours: Decimal
    kind: str = DEFAULT_KIND


def parse_hours(text):
    """Decimal hours such as `7.5`, or None when the text is not a number."""
    try:
        hours = Decimal(text.strip())
    except InvalidOperation:
        return None
    if not hours.is_finite():
        return None
    return hours.quantize(HUNDREDTH, rounding=ROUND_HALF_UP)


def format_hours(hours):
    return f"{hours:.2f}"
