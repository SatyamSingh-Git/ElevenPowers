"""Closing a collection day: write the carrier manifest for everything booked to ship that day."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..core.errors import ManifestError
from ..core.shipment import BOOKED, MANIFESTED
from ..formats.manifest import manifest_filename, write_manifest
from ..storage.shipments import ShipmentStore


@dataclass(frozen=True)
class ClosedDay:
    day: date
    path: Path
    shipments: int


def close_day(settings, day):
    path = settings.manifest_dir / manifest_filename(day)
    if path.exists():
        raise ManifestError(f"manifest for {day.isoformat()} is already closed")
    store = ShipmentStore(settings.store_path)
    shipments = store.find(ship_date=day, status=BOOKED)
    if not shipments:
        raise ManifestError(f"no shipments to manifest for {day.isoformat()}")
    write_manifest(path, shipments)
    for shipment in shipments:
        shipment.status = MANIFESTED
    store.save()
    return ClosedDay(day, path, len(shipments))
