"""The waiting-list file: JSON, one object per waiting patient."""
from datetime import date, datetime
import json
from pathlib import Path

from ..errors import StorageError
from ..services.waitlist import WaitEntry

DEFAULT_NAME = "waitlist.json"


def _encode(entry):
    return {
        "patient": entry.patient,
        "phone": entry.phone,
        "practitioner": entry.practitioner,
        "earliest": entry.earliest.isoformat(),
        "latest": entry.latest.isoformat(),
        "added": entry.added.isoformat(timespec="minutes"),
    }


def _decode(raw, where):
    try:
        return WaitEntry(
            patient=raw["patient"],
            phone=raw["phone"],
            practitioner=raw["practitioner"],
            earliest=date.fromisoformat(raw["earliest"]),
            latest=date.fromisoformat(raw["latest"]),
            added=datetime.fromisoformat(raw["added"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError(f"{where}: bad waiting-list entry ({error})") from None


def load_waitlist(path=DEFAULT_NAME):
    path = Path(path)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StorageError(f"{path} is not valid JSON: {error.msg}") from None
    if not isinstance(raw, list):
        raise StorageError(f"{path} must hold a list")
    return [_decode(entry, f"{path} entry {number}") for number, entry in enumerate(raw, 1)]


def save_waitlist(waitlist, path=DEFAULT_NAME):
    text = json.dumps([_encode(entry) for entry in waitlist], indent=2)
    Path(path).write_text(text + "\n", encoding="utf-8")
