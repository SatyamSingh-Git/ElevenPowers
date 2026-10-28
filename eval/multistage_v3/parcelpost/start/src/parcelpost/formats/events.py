"""The tracking events file: one JSON object per line, appended as scans arrive."""
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from ..core.clock import format_timestamp, parse_timestamp
from ..storage.files import append_lines


@dataclass(frozen=True)
class Event:
    tracking_number: str
    code: str
    at: datetime
    depot: str


def append_events(path, events):
    append_lines(path, [json.dumps({"number": event.tracking_number, "code": event.code,
                                    "at": format_timestamp(event.at), "depot": event.depot})
                        for event in events])


def read_events(path):
    path = Path(path)
    if not path.is_file():
        return []
    events = []
    for text in path.read_text(encoding="utf-8").splitlines():
        if text.strip():
            record = json.loads(text)
            events.append(Event(record["number"], record["code"], parse_timestamp(record["at"]),
                                record["depot"]))
    return events


def latest_by_number(events):
    """The most recent event for each tracking number; of two at the same minute, the later in the file."""
    latest = {}
    for event in events:
        current = latest.get(event.tracking_number)
        if current is None or event.at >= current.at:
            latest[event.tracking_number] = event
    return latest
