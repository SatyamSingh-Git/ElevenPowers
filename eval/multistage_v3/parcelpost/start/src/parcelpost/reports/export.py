"""Shipment export for the accounts team: CSV of everything collected in a period."""
import csv
import io

from ..core.clock import format_timestamp
from ..core.money import format_amount
from ..storage.shipments import ShipmentStore

EXPORT_COLUMNS = ("tracking_number", "account", "service", "booked_at", "ship_date", "status",
                  "charge", "return_of")


def export_shipments(settings, start, end):
    shipments = [shipment for shipment in ShipmentStore(settings.store_path).find()
                 if start <= shipment.ship_date <= end]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for shipment in shipments:
        writer.writerow([
            shipment.tracking_number,
            shipment.account,
            shipment.service,
            format_timestamp(shipment.booked_at),
            shipment.ship_date.isoformat(),
            shipment.status,
            format_amount(shipment.total),
            shipment.return_of or "",
        ])
    return buffer.getvalue()
