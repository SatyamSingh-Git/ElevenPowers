"""Importing the carrier's scan file: record every scan and move shipments to the status it implies."""
from dataclasses import dataclass
import re

from ..core.errors import ScanError
from ..core.shipment import DELIVERED, EXCEPTION, IN_TRANSIT, RETURNED
from ..formats.events import Event, append_events, latest_by_number, read_events
from ..formats.scanfile import parse_scan_file
from ..storage.shipments import ShipmentStore
from .notifications import queue_notices

SCAN_CODES = {
    "PU": IN_TRANSIT,   # collected from the depot
    "AR": IN_TRANSIT,   # arrived at a hub
    "DP": IN_TRANSIT,   # left a hub
    "OFD": IN_TRANSIT,  # on the van for delivery today
    "DL": DELIVERED,
    "EX": EXCEPTION,    # delivery problem; the carrier's note is on their portal
    "RT": RETURNED,
}
NUMBER = re.compile(r"^PP[0-9]{9}GB$")


@dataclass(frozen=True)
class ScanImport:
    scans: int
    shipments: int


def import_scans(settings, text):
    """Record a scan file. The whole file is checked first, so a bad line records nothing."""
    rows = parse_scan_file(text)
    store = ShipmentStore(settings.store_path)
    for row in rows:
        if not _plausible_number(row.tracking_number):
            raise ScanError(f"line {row.line}: invalid tracking number {row.tracking_number}")
        if row.code not in SCAN_CODES:
            raise ScanError(f"line {row.line}: unknown scan code {row.code}")
        if row.tracking_number not in store:
            raise ScanError(f"line {row.line}: no shipment {row.tracking_number}")
    events = [Event(row.tracking_number, row.code, row.at, row.depot) for row in rows]
    append_events(settings.events_path, events)
    touched = {event.tracking_number for event in events}
    history = [event for event in read_events(settings.events_path) if event.tracking_number in touched]
    for number, event in latest_by_number(history).items():
        store.get(number).status = SCAN_CODES[event.code]
    store.save()
    queue_notices(settings, events, store)
    return ScanImport(len(events), len(touched))


def _plausible_number(number):
    """Layout and check digit as we issue them, so a misread number is refused before anything is recorded."""
    if not NUMBER.match(number):
        return False
    serial, check = number[2:10], int(number[10])
    total = sum(int(digit) * (3 if position % 2 == 0 else 1) for position, digit in enumerate(serial))
    return (10 - total % 10) % 10 == check
