"""The daily report: everything collected on one day, by status and by service."""
from dataclasses import dataclass
from datetime import date

from ..core.money import format_amount
from ..core.shipment import BOOKED, DELIVERED, EXCEPTION, IN_TRANSIT, MANIFESTED, RETURNED
from ..core.units import format_kg
from ..rating.tariff import service_name, services
from ..storage.shipments import ShipmentStore
from .tables import render_table

STATUS_COLUMNS = (
    (BOOKED, "Booked"),
    (MANIFESTED, "Manifested"),
    (IN_TRANSIT, "In transit"),
    (DELIVERED, "Delivered"),
    (EXCEPTION, "Exception"),
    (RETURNED, "Returned"),
)


@dataclass(frozen=True)
class ServiceTotals:
    service: str
    shipments: int
    weight_grams: int
    revenue: int


@dataclass(frozen=True)
class DailySummary:
    day: date
    by_status: dict
    by_service: tuple

    @property
    def shipments(self):
        return sum(totals.shipments for totals in self.by_service)

    @property
    def weight_grams(self):
        return sum(totals.weight_grams for totals in self.by_service)

    @property
    def revenue(self):
        return sum(totals.revenue for totals in self.by_service)


def daily_summary(settings, day):
    shipments = ShipmentStore(settings.store_path).find(ship_date=day)
    by_status = {status: 0 for status, _ in STATUS_COLUMNS}
    for shipment in shipments:
        by_status[shipment.status] += 1
    by_service = []
    for service in services():
        mine = [shipment for shipment in shipments if shipment.service == service]
        if mine:
            by_service.append(ServiceTotals(
                service, len(mine),
                sum(shipment.parcel.weight_grams for shipment in mine),
                sum(shipment.total for shipment in mine)))
    return DailySummary(day, by_status, tuple(by_service))


def render_daily(summary):
    if not summary.shipments:
        return f"Nothing collected on {summary.day.isoformat()}."
    services_table = render_table(
        ("Service", "Shipments", "Weight kg", "Revenue"),
        [(service_name(totals.service), totals.shipments, format_kg(totals.weight_grams),
          format_amount(totals.revenue)) for totals in summary.by_service]
        + [("Total", summary.shipments, format_kg(summary.weight_grams), format_amount(summary.revenue))],
        right=("Shipments", "Weight kg", "Revenue"))
    status_table = render_table(
        ("Status", "Shipments"),
        [(title, summary.by_status[status]) for status, title in STATUS_COLUMNS],
        right=("Shipments",))
    return "\n\n".join([f"Daily report for {summary.day.isoformat()}", services_table, status_table])
