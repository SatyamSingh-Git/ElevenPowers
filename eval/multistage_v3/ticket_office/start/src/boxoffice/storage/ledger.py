"""The ledger: every movement of money, appended one JSON object per line.

An entry records its `kind`, the `date` it happened, the `order` and
`performance` it belongs to, how many `tickets` moved, the `amount` in pence and
the `payment` method. Money taken is positive and money paid back is negative,
so the amounts for any stretch of time add up to what the box office kept.
"""
import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


class Ledger:
    def __init__(self, root):
        self.path = Path(root) / LEDGER_FILE

    def record_entry(self, kind, *, at, order, performance, tickets, amount, payment):
        entry = {"kind": kind, "date": at.date().isoformat(), "order": order,
                 "performance": performance, "tickets": tickets, "amount": amount,
                 "payment": payment}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry

    def read_entries(self):
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def entries_on(self, day):
        return [entry for entry in self.read_entries() if entry["date"] == day]
