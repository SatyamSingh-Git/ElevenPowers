"""The irrigation plan, ``irrigation.csv``: the latest suggestion for each zone."""
import csv
from pathlib import Path

PLAN_COLUMNS = ["zone", "minutes", "reason"]


def write_plan(path, suggestions):
    """Replace the plan with these suggestions, in the order given."""
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(PLAN_COLUMNS)
        for suggestion in suggestions:
            writer.writerow([suggestion.zone, suggestion.minutes, suggestion.reason])
