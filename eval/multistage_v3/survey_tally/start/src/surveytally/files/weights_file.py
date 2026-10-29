"""Weights files: a CSV of respondent ids and the weight each one carries.

The `weight` command writes one; weights from a panel provider can be read the same way.
"""
import csv
from pathlib import Path

from ..model.errors import WeightingError

WEIGHT_COLUMNS = ('respondent', 'weight')
WEIGHT_DECIMALS = 6


def read_weights(path):
    path = Path(path)
    weights = {}
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in WEIGHT_COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise WeightingError(f'{path.name}: missing column {missing[0]}')
        for number, row in enumerate(reader, start=2):
            respondent = row['respondent'].strip()
            try:
                weight = float(row['weight'])
            except ValueError:
                raise WeightingError(f'{path.name} row {number}: weight is not a number: {row["weight"]}') from None
            if weight <= 0:
                raise WeightingError(f'{path.name} row {number}: weight must be above 0, got {weight}')
            if respondent in weights:
                raise WeightingError(f'{path.name} row {number}: respondent {respondent} appears twice')
            weights[respondent] = weight
    return weights


def write_weights(weights, path):
    with Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(WEIGHT_COLUMNS)
        for respondent, weight in weights.items():
            writer.writerow([respondent, f'{weight:.{WEIGHT_DECIMALS}f}'])
