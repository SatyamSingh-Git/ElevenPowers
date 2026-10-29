"""Brings data directories written by older releases up to the current format.

Each step names the release that introduced the change and upgrades one file
in place. Steps are safe to run twice: a file already in the current format is
left as it is.
"""
import json
from pathlib import Path

from .jsonstore import HOLDS_FILE, ORDERS_FILE, PERFORMANCES_FILE


def _performances_cancelled(data):
    """1.2: performances gained `cancelled`."""
    changed = False
    for performance in data:
        if "cancelled" not in performance:
            performance["cancelled"] = False
            changed = True
    return changed


def _orders_customer(data):
    """1.3: orders gained an optional `customer` email."""
    changed = False
    for order in data.values():
        if "customer" not in order:
            order["customer"] = None
            changed = True
    return changed


def _holds_status(data):
    """1.3: holds stopped being deleted when sold; `sold` became a status."""
    changed = False
    for hold in data.values():
        if "status" not in hold:
            hold["status"] = "sold" if hold.get("order") else "active"
            changed = True
        if "order" not in hold:
            hold["order"] = None
            changed = True
    return changed


STEPS = [
    (PERFORMANCES_FILE, _performances_cancelled),
    (ORDERS_FILE, _orders_customer),
    (HOLDS_FILE, _holds_status),
]


def upgrade(root):
    """Run every step against `root`; returns the names of the files that changed."""
    root = Path(root)
    changed = []
    for name, step in STEPS:
        path = root / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if step(data):
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            if name not in changed:
                changed.append(name)
    return changed
