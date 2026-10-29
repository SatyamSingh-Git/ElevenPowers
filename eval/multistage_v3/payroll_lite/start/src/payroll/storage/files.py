"""Where things live in a data directory, and writing a file without leaving half of one behind."""
import os
from pathlib import Path


class DataDir:
    def __init__(self, root):
        self.root = Path(root)

    @property
    def employees(self):
        return self.root / "employees.json"

    @property
    def runs(self):
        return self.root / "runs"

    def run(self, period_id):
        return self.runs / f"{period_id}.json"

    def timesheet(self, period_id):
        return self.root / "timesheets" / f"{period_id}.csv"

    def bank_file(self, period_id):
        return self.root / "bank" / f"{period_id}.csv"


def write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(text, encoding="utf-8", newline="")
    os.replace(partial, path)
