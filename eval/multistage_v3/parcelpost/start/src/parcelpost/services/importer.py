"""Bulk booking from the orders CSV the web shop exports."""
import csv
from dataclasses import dataclass
import io

from ..core.address import make_address
from ..core.errors import ParcelpostError, ValidationError
from ..core.money import parse_amount
from ..core.parcel import Parcel
from ..core.units import kg_to_grams, parse_size
from .booking import Order, book

REQUIRED = ("account", "name", "line1", "town", "postcode", "weight_kg", "size_cm")
OPTIONAL = ("service", "residential", "signature", "value")
FLAGS = {"": False, "0": False, "no": False, "false": False, "1": True, "yes": True, "true": True}


@dataclass(frozen=True)
class ImportReport:
    booked: list
    errors: list


def import_orders(settings, text, *, clock):
    """Book every row that can be booked; report the others by line number instead of stopping."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [column for column in REQUIRED if column not in (reader.fieldnames or [])]
    if missing:
        raise ValidationError(f"orders file is missing columns: {', '.join(missing)}")
    booked, errors = [], []
    for line, row in enumerate(reader, start=2):
        try:
            booked.append(book(settings, _order(row), clock=clock))
        except ParcelpostError as error:
            errors.append((line, str(error)))
    return ImportReport(booked, errors)


def _order(row):
    cells = {column: (row.get(column) or "").strip() for column in REQUIRED + OPTIONAL}
    length, width, height = parse_size(cells["size_cm"])
    parcel = Parcel(weight_grams=kg_to_grams(cells["weight_kg"]), length_cm=length, width_cm=width,
                    height_cm=height, declared_pence=parse_amount(cells["value"] or "0"))
    return Order(
        account=cells["account"].upper(),
        recipient=make_address(cells["name"], cells["line1"], cells["town"], cells["postcode"]),
        parcel=parcel,
        service=cells["service"].lower() or None,
        residential=_flag(cells["residential"]),
        signature=_flag(cells["signature"]),
    )


def _flag(text):
    try:
        return FLAGS[text.lower()]
    except KeyError:
        raise ValidationError(f"invalid yes/no value: {text}") from None
