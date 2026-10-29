"""Where each file lives inside a data directory."""
from pathlib import Path


class DataDir:
    def __init__(self, root):
        self.root = Path(root)

    @property
    def settings(self):
        return self.root / "settings.json"

    @property
    def layout(self):
        return self.root / "layout.json"

    @property
    def thresholds(self):
        return self.root / "thresholds.json"

    @property
    def calibration(self):
        return self.root / "calibration.json"

    @property
    def readings(self):
        return self.root / "readings.csv"

    @property
    def alerts(self):
        return self.root / "alerts.jsonl"

    @property
    def plan(self):
        return self.root / "irrigation.csv"

    @property
    def valves(self):
        return self.root / "valves.txt"

    @property
    def archive(self):
        return self.root / "archive"

    @property
    def outbox(self):
        return self.root / "outbox"
