"""On-time performance: how many deliveries in a period arrived by their expected day."""
from dataclasses import dataclass

from ..core.shipment import DELIVERED
from ..formats.events import latest_by_number, read_events
from ..rating.tariff import service_name, services
from ..storage.shipments import ShipmentStore
from .tables import render_table


@dataclass(frozen=True)
class ServicePerformance:
    service: str
    delivered: int
    on_time: int

    @property
    def percent(self):
        return round(100 * self.on_time / self.delivered, 1) if self.delivered else None


def on_time_performance(settings, start, end):
    """Per service, shipments delivered between `start` and `end` inclusive, and how many on time."""
    store = ShipmentStore(settings.store_path)
    latest = latest_by_number(read_events(settings.events_path))
    counts = {service: [0, 0] for service in services()}
    for shipment in store.find(status=DELIVERED):
        # A delivered shipment's latest scan is the one that delivered it.
        delivered_on = latest[shipment.tracking_number].at.date()
        if start <= delivered_on <= end:
            counts[shipment.service][0] += 1
            counts[shipment.service][1] += delivered_on <= shipment.expected_delivery
    return [ServicePerformance(service, delivered, on_time)
            for service, (delivered, on_time) in counts.items() if delivered]


def render_performance(rows, start, end):
    heading = f"On-time delivery {start.isoformat()} to {end.isoformat()}"
    if not rows:
        return heading + "\n\nNo deliveries in this period."
    table = render_table(
        ("Service", "Delivered", "On time", "Percent"),
        [(service_name(row.service), row.delivered, row.on_time, f"{row.percent:.1f}") for row in rows],
        right=("Delivered", "On time", "Percent"))
    return heading + "\n\n" + table
