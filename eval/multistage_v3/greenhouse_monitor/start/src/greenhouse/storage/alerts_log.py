"""The alerts log, ``alerts.jsonl``: one JSON object per alert, oldest first."""
import json
from pathlib import Path

from ..core.clock import format_timestamp, parse_timestamp


def alert_record(alert):
    """The alert as the log stores it."""
    return {
        "at": format_timestamp(alert.at),
        "zone": alert.zone,
        "sensor": alert.sensor,
        "kind": alert.kind,
        "code": alert.code,
        "value": alert.value,
        "limit": alert.limit,
        "unit": alert.unit,
    }


def append_alerts(path, alerts):
    with Path(path).open("a", encoding="utf-8") as handle:
        for alert in alerts:
            handle.write(json.dumps(alert_record(alert)) + "\n")


def read_alerts(path, *, day=None):
    """Logged alert records, optionally only those raised on one day."""
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if day is None or parse_timestamp(record["at"]).date() == day:
            records.append(record)
    return records


def logged_keys(records):
    """The (day, sensor, code) of each record, to match against ``Alert.key``."""
    return {(parse_timestamp(r["at"]).date(), r["sensor"], r["code"]) for r in records}
