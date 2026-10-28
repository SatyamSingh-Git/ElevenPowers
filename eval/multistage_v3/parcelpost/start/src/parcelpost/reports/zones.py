"""Where parcels went: shipments and revenue by zone over a period."""
from dataclasses import dataclass

from ..core.money import format_amount
from ..storage.shipments import ShipmentStore
from .tables import render_table


@dataclass(frozen=True)
class ZoneTotals:
    zone: int
    shipments: int
    revenue: int


def zone_totals(settings, start, end):
    totals = {}
    for shipment in ShipmentStore(settings.store_path).find():
        if start <= shipment.ship_date <= end:
            count, revenue = totals.get(shipment.quote.zone, (0, 0))
            totals[shipment.quote.zone] = (count + 1, revenue + shipment.total)
    return [ZoneTotals(zone, count, revenue) for zone, (count, revenue) in sorted(totals.items())]


def render_zone_totals(rows, start, end):
    heading = f"Shipments by zone {start.isoformat()} to {end.isoformat()}"
    if not rows:
        return heading + "\n\nNo shipments in this period."
    shipments = sum(row.shipments for row in rows)
    table = render_table(
        ("Zone", "Shipments", "Share", "Revenue"),
        [(row.zone, row.shipments, f"{100 * row.shipments / shipments:.1f}%", format_amount(row.revenue))
         for row in rows],
        right=("Zone", "Shipments", "Share", "Revenue"))
    return heading + "\n\n" + table
