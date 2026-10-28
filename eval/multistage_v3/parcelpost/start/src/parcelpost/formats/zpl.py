"""Shipping labels as ZPL for printers that take it directly (4x6 inch stock, 203 dpi)."""
from ..core.units import format_kg

LEFT = 40
LINE_HEIGHT = 36


def _escape(text):
    # ^ and ~ start ZPL commands; the carrier's printers accept them hex-escaped after ^FH.
    return text.replace("_", "_5F").replace("^", "_5E").replace("~", "_7E")


def _field(y, text, size=30):
    return f"^FO{LEFT},{y}^A0N,{size},{size}^FH^FD{_escape(text)}^FS"


def render_zpl(shipment, service_name):
    recipient = shipment.recipient
    fields = [
        _field(30, f"{service_name.upper()}  ZONE {shipment.quote.zone}", size=50),
        _field(110, "TO:"),
    ]
    y = 110 + LINE_HEIGHT
    for line in recipient.lines():
        fields.append(_field(y, line.upper(), size=40))
        y += LINE_HEIGHT + 10
    y += LINE_HEIGHT
    fields.append(_field(y, f"WEIGHT {format_kg(shipment.parcel.weight_grams)} KG"))
    fields.append(_field(y + LINE_HEIGHT, f"SHIP DATE {shipment.ship_date.isoformat()}"))
    fields.append(_field(y + 2 * LINE_HEIGHT, f"ACCOUNT {shipment.account}"))
    if shipment.signature:
        fields.append(_field(y + 3 * LINE_HEIGHT, "SIGNATURE REQUIRED"))
    barcode = f"^FO{LEFT},900^BY3^BCN,160,Y,N,N^FD{shipment.tracking_number}^FS"
    return "\n".join(["^XA", "^CI28", *fields, barcode, "^XZ"]) + "\n"
