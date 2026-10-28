"""The carrier manifest: one CSV per collection day listing every shipment handed over."""
import csv
import io

from ..storage.files import write_atomic

COLUMNS = ("tracking_number", "account", "service", "zone", "weight_g", "billable_g", "charge",
           "surcharges")


def manifest_filename(day):
    return f"manifest-{day.isoformat()}.csv"


def write_manifest(path, shipments):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for shipment in _manifest_order(shipments):
        writer.writerow(_manifest_row(shipment))
    write_atomic(path, buffer.getvalue())


def _manifest_order(shipments):
    return sorted(shipments, key=lambda shipment: (shipment.account, shipment.tracking_number))


def _manifest_row(shipment):
    quote = shipment.quote
    return {
        "tracking_number": shipment.tracking_number,
        "account": shipment.account,
        "service": shipment.service,
        "zone": quote.zone,
        "weight_g": shipment.parcel.weight_grams,
        "billable_g": quote.billable_grams,
        "charge": quote.total,
        "surcharges": "+".join(quote.surcharge_codes),
    }
