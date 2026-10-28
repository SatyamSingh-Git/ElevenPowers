"""The carrier's invoice to us: CSV, one charged shipment per line, amounts in pounds."""
import csv
import io

from ..core.errors import ValidationError
from ..core.money import parse_amount

HEADER = ["tracking_number", "amount"]


def parse_carrier_invoice(text):
    """Pence charged per tracking number. A number charged twice is an error in the file."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or [cell.strip().lower() for cell in rows[0]] != HEADER:
        raise ValidationError("carrier invoice must start with the header " + ",".join(HEADER))
    charged = {}
    for line, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(HEADER):
            raise ValidationError(f"carrier invoice line {line}: expected {len(HEADER)} fields")
        number, amount = row[0].strip().upper(), row[1].strip()
        if number in charged:
            raise ValidationError(f"carrier invoice line {line}: {number} is charged twice")
        charged[number] = parse_amount(amount)
    return charged
