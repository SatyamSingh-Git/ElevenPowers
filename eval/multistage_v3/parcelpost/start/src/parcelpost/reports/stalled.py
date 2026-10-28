"""The stalled report: shipments still on their way whose last scan is too long ago."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter

from ..core.clock import format_timestamp
from ..core.shipment import FINAL_STATUSES
from ..formats.events import latest_by_number, read_events
from ..storage.shipments import ShipmentStore
from .tables import render_table


@dataclass(frozen=True)
class Stalled:
    tracking_number: str
    account: str
    status: str
    last_scan: datetime
    depot: str
    hours: int


def find_stalled(settings, now):
    """Shipments not yet delivered or returned with no scan for more than `stale_hours`, oldest first."""
    store = ShipmentStore(settings.store_path)
    limit = timedelta(hours=settings.stale_hours)
    stalled = []
    for number, event in latest_by_number(read_events(settings.events_path)).items():
        shipment = store.get(number)
        waited = now - event.at
        if shipment.status not in FINAL_STATUSES and waited > limit:
            stalled.append(Stalled(number, shipment.account, shipment.status, event.at, event.depot,
                                   int(waited.total_seconds()) // 3600))
    return sorted(stalled, key=attrgetter("last_scan", "tracking_number"))


def render_stalled(stalled, stale_hours):
    if not stalled:
        return f"No shipments without a scan for more than {stale_hours} hours."
    return render_table(
        ("Tracking number", "Account", "Status", "Last scan", "Depot", "Hours"),
        [(row.tracking_number, row.account, row.status, format_timestamp(row.last_scan), row.depot,
          row.hours) for row in stalled],
        right=("Hours",))
