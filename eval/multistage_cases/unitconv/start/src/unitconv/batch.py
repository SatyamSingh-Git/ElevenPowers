"""Batch conversion: a CSV of `quantity,target` rows in, a CSV of results out."""
import csv

from .convert import convert
from .errors import UnitError
from .formatting import format_number, result_record
from .quantity import parse_quantity

COLUMNS = ('input', 'target', 'value', 'unit', 'error')


def convert_file(source, destination, settings):
    """Convert every row of `source` into `destination`; returns (converted, failed) row counts.

    Blank rows and rows whose first cell starts with `#` are skipped. A row that
    cannot be converted is still written, with the reason in its error column.
    """
    converted = failed = 0
    with open(source, newline='', encoding='utf-8') as infile, \
            open(destination, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(COLUMNS)
        for row in csv.reader(infile):
            if not row or not row[0].strip() or row[0].lstrip().startswith('#'):
                continue
            row = [cell.strip() for cell in row]
            try:
                if len(row) != 2:
                    raise UnitError(f'expected 2 columns, got {len(row)}')
                text, target = row
                result = convert(parse_quantity(text), target,
                                 precision=settings.precision, rounding=settings.rounding)
                record = result_record(text, result, style=settings.style)
                writer.writerow([text, target, format_number(record['value']), record['unit'], ''])
                converted += 1
            except UnitError as error:
                writer.writerow([*(row + ['', ''])[:2], '', '', str(error)])
                failed += 1
    return converted, failed
