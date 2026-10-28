"""Housekeeping: archive finished shipments and check the data directory hangs together."""
from collections import defaultdict
import json

from ..core.shipment import BOOKED, FINAL_STATUSES
from ..formats.events import read_events
from ..formats.manifest import manifest_filename
from ..storage.files import append_lines
from ..storage.shipments import ShipmentStore, encode_shipment
from .booking import label_path


def archive_finished(settings, before):
    """Move delivered and returned shipments collected before `before` into yearly archive files."""
    store = ShipmentStore(settings.store_path)
    finished = [shipment for shipment in store.find()
                if shipment.status in FINAL_STATUSES and shipment.ship_date < before]
    by_year = defaultdict(list)
    for shipment in finished:
        by_year[shipment.ship_date.year].append(json.dumps(encode_shipment(shipment)))
    for year, lines in by_year.items():
        append_lines(settings.data_dir / "archive" / f"shipments-{year}.jsonl", lines)
    for shipment in finished:
        store.remove(shipment.tracking_number)
    store.save()
    return len(finished)


def check_data(settings):
    """Problems a person should look at, one sentence each; an empty list means none were found."""
    store = ShipmentStore(settings.store_path)
    problems = []
    scanned = {event.tracking_number for event in read_events(settings.events_path)}
    for shipment in store.find():
        if not label_path(settings, shipment).is_file():
            problems.append(f"{shipment.tracking_number} has no label")
        manifest = settings.manifest_dir / manifest_filename(shipment.ship_date)
        if shipment.status != BOOKED and not manifest.is_file():
            problems.append(f"{shipment.tracking_number} is {shipment.status} but {manifest.name} is missing")
        if shipment.status in FINAL_STATUSES and shipment.tracking_number not in scanned:
            problems.append(f"{shipment.tracking_number} is {shipment.status} with no scans recorded")
    return problems
