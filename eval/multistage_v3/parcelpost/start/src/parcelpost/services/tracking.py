"""Tracking: where a shipment is, from the store and the events file."""
from dataclasses import dataclass

from ..core.shipment import FINAL_STATUSES
from ..formats.events import read_events
from ..storage.shipments import ShipmentStore


@dataclass(frozen=True)
class Tracking:
    shipment: object
    events: tuple

    @property
    def status(self):
        return self.shipment.status

    @property
    def last_scan(self):
        return self.events[-1] if self.events else None

    def late_on(self, day):
        return self.status not in FINAL_STATUSES and day > self.shipment.expected_delivery


def track(settings, number):
    shipment = ShipmentStore(settings.store_path).get(number.strip().upper())
    events = sorted((event for event in read_events(settings.events_path)
                     if event.tracking_number == shipment.tracking_number),
                    key=lambda event: event.at)
    return Tracking(shipment, tuple(events))
