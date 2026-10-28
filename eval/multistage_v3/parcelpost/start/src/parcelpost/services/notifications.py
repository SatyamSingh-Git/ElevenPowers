"""Shipper notifications: a message to a registered account when one of its parcels moves.

Messages are queued in `outbox.jsonl`; the mail relay on the depot server sends and removes them.
Only the scans a shipper cares about produce a message, and only for accounts with an email.
"""
from dataclasses import asdict, dataclass
import json

from ..core.clock import format_timestamp
from ..storage.accounts import AccountBook
from ..storage.files import append_lines

NOTICES = {
    "PU": ("Collected", "{number} to {town} was collected from the depot."),
    "OFD": ("Out for delivery", "{number} to {town} is on the van and should arrive today."),
    "DL": ("Delivered", "{number} to {town} was delivered at {time}."),
    "EX": ("Delivery problem", "{number} to {town} could not be delivered; the carrier will try again."),
    "RT": ("Returning", "{number} to {town} is on its way back to the depot."),
}


@dataclass(frozen=True)
class Notice:
    to: str
    subject: str
    body: str
    at: str


def notices_for(events, store, accounts):
    notices = []
    for event in events:
        if event.code not in NOTICES:
            continue
        shipment = store.get(event.tracking_number)
        account = accounts.find(shipment.account)
        if account is None:
            continue
        subject, template = NOTICES[event.code]
        body = template.format(number=shipment.tracking_number, town=shipment.recipient.town,
                               time=event.at.strftime("%H:%M"))
        notices.append(Notice(account.email, f"{subject}: {shipment.tracking_number}", body,
                              format_timestamp(event.at)))
    return notices


def queue_notices(settings, events, store):
    notices = notices_for(events, store, AccountBook(settings.accounts_path))
    append_lines(settings.data_dir / "outbox.jsonl", [json.dumps(asdict(notice)) for notice in notices])
    return len(notices)
