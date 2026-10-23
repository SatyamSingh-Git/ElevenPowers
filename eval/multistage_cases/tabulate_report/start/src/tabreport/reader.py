"""Reading CSV exports into rows of text."""
import csv

from .dialect import Dialect
from .errors import ReportError


def read_csv(path, dialect=None, required=()):
    """Every data row of ``path`` as a dict keyed by the header row.

    Cells keep their text, stripped of surrounding whitespace; numbers are
    parsed later by the measures that need them. ``required`` names columns
    the header must have.
    """
    dialect = dialect or Dialect()
    rows = []
    try:
        with open(path, newline="", encoding=dialect.encoding) as handle:
            records = csv.reader(handle, delimiter=dialect.delimiter, quotechar=dialect.quotechar)
            header = _header(records)
            for name in required:
                if name not in header:
                    raise ReportError(f"missing column: {name}")
            for record in records:
                if _blank(record):
                    if dialect.skip_blank:
                        continue
                    record = [""] * len(header)
                if len(record) != len(header):
                    raise ReportError(
                        f"wrong field count: line {records.line_num} has {len(record)}, expected {len(header)}")
                rows.append(dict(zip(header, (cell.strip() for cell in record))))
    except UnicodeDecodeError:
        raise ReportError(f"cannot decode: {path} is not {dialect.encoding}") from None
    return rows


def _header(records):
    for record in records:
        if not _blank(record):
            break
    else:
        raise ReportError("empty input: no header row")
    header = [name.strip() for name in record]
    seen = set()
    for name in header:
        if not name:
            raise ReportError(f"empty column name: line {records.line_num}")
        if name in seen:
            raise ReportError(f"duplicate column: {name}")
        seen.add(name)
    return header


def _blank(record):
    return not any(cell.strip() for cell in record)
