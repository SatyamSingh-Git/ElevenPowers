"""CSV files from other systems, and what importing one did."""
import csv
from dataclasses import dataclass, field

from ..errors import FleetError


@dataclass
class ImportResult:
    imported: int = 0
    skipped: list = field(default_factory=list)
    rejected: list = field(default_factory=list)

    def summary(self):
        return (f"imported {self.imported}, skipped {len(self.skipped)}, "
                f"rejected {len(self.rejected)}")


def read_rows(path, columns):
    """(line number, row) for each data row; the header is line 1."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in columns if name not in (reader.fieldnames or [])]
        if missing:
            raise FleetError("E145", path=str(path), columns=",".join(missing))
        for row in reader:
            yield reader.line_num, {name: (row[name] or "").strip() for name in columns}
