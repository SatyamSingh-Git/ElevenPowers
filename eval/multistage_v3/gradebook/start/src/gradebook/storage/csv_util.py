"""Reading teachers' CSV files: header checks, line numbers and score cells."""
import csv

from ..errors import ImportFailed

EXCUSED = "EX"


def read_table(path, required):
    """The header and (line number, row) pairs of a CSV file that has every required column."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = [name.strip() for name in reader.fieldnames or []]
        reader.fieldnames = header
        for column in required:
            if column not in header:
                raise ImportFailed(f"{path.name}: missing column {column}")
        rows = []
        for row in reader:
            rows.append((reader.line_num, {key: (value or "").strip() for key, value in row.items()}))
    return header, rows


def parse_cell(cell, line):
    """A score cell as ("blank", None), ("excused", None) or ("points", number)."""
    if cell == "":
        return "blank", None
    if cell == EXCUSED:
        return "excused", None
    try:
        points = float(cell)
    except ValueError:
        raise ImportFailed(f"line {line}: cannot read points {cell}") from None
    return "points", points


def parse_day(cell, line):
    if cell == "":
        return None
    try:
        return int(cell)
    except ValueError:
        raise ImportFailed(f"line {line}: cannot read day {cell}") from None
