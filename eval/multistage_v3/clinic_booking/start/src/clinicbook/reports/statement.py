"""Patient statements, read back from the charges file the `fees` command writes."""
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..errors import StorageError


@dataclass(frozen=True)
class StatementLine:
    day: date
    booking: str
    reason: str
    amount: Decimal


@dataclass(frozen=True)
class Statement:
    phone: str
    patient: str
    lines: tuple

    @property
    def total(self):
        return sum((line.amount for line in self.lines), Decimal("0.00"))


def _line(row, where):
    try:
        return StatementLine(date.fromisoformat(row["day"]), row["booking"], row["reason"], Decimal(row["amount"]))
    except (ValueError, InvalidOperation):
        raise StorageError(f"{where}: not a charge row") from None


def statement_from_file(path, phone):
    """Everything charged to `phone` in the charges file, in file order."""
    path = Path(path)
    if not path.exists():
        raise StorageError(f"no charges file at {path}")
    lines, patient = [], ""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["phone"] != phone:
                continue
            patient = row["patient"]
            lines.append(_line(row, f"{path}:{reader.line_num}"))
    return Statement(phone, patient, tuple(lines))


def render_statement(statement, settings):
    if not statement.lines:
        return [f"Nothing owed by {statement.phone}"]
    lines = [f"Statement for {statement.patient} ({statement.phone})"]
    for line in statement.lines:
        lines.append(f"  {line.day:%d %b %Y}  {line.booking}  {line.reason:<10} {settings.money(line.amount):>10}")
    lines.append(f"Total: {settings.money(statement.total)}")
    return lines
