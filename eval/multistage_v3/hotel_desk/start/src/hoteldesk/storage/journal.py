"""The audit journal: one CSV line for each business date the night audit closes.

Accounting collects the file at month end, and the revenue report reads it back.
"""
import csv
from pathlib import Path

JOURNAL_FIELDS = (
    "business_date",
    "rooms_sold",
    "rooms_available",
    "room_revenue",
    "tax_revenue",
    "other_revenue",
    "payments",
)


def append_entry(path, entry):
    path = Path(path)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=JOURNAL_FIELDS, lineterminator="\n")
        if is_new:
            writer.writeheader()
        writer.writerow({**entry, "business_date": entry["business_date"].isoformat()})
