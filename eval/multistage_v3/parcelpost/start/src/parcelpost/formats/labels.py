"""Shipping labels: fixed-width text for the depot's thermal printers, or ZPL."""
from ..core.units import format_kg
from .zpl import render_zpl

LABEL_WIDTH = 40
_INNER = LABEL_WIDTH - 4


def render_text(shipment, service_name):
    border = "+" + "-" * (LABEL_WIDTH - 2) + "+"
    rows = [
        f"{service_name.upper()}  ZONE {shipment.quote.zone}",
        "",
        "TO:",
        *(line.upper() for line in shipment.recipient.lines()),
        "",
        f"WEIGHT {format_kg(shipment.parcel.weight_grams)} KG",
        f"SHIP DATE {shipment.ship_date.isoformat()}",
        f"ACCOUNT {shipment.account}",
    ]
    if shipment.signature:
        rows.append("SIGNATURE REQUIRED")
    body = [f"| {row[:_INNER]:<{_INNER}} |" for row in rows]
    number = f"| {shipment.tracking_number:^{_INNER}} |"
    return "\n".join([border, *body, border, number, border]) + "\n"


# The `label_format` setting picks one of these: file extension and renderer.
LABEL_FORMATS = {
    "text": (".txt", render_text),
    "zpl": (".zpl", render_zpl),
}


def label_filename(tracking_number, label_format):
    return tracking_number + LABEL_FORMATS[label_format][0]


def render_label(shipment, service_name, label_format):
    return LABEL_FORMATS[label_format][1](shipment, service_name)
