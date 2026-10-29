"""Weighting targets: the population's share of each answer to a question.

A targets file is a CSV with the columns `question`, `option` and `share`;
the shares for one question add up to 1.
"""
import csv
from pathlib import Path

from ..model.errors import WeightingError

TARGET_COLUMNS = ('question', 'option', 'share')
SHARE_TOLERANCE = 0.001


def read_targets(path):
    """Shares by question id, then by option code."""
    path = Path(path)
    targets = {}
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in TARGET_COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise WeightingError(f'{path.name}: missing column {missing[0]}')
        for number, row in enumerate(reader, start=2):
            question, option = row['question'].strip(), row['option'].strip()
            try:
                share = float(row['share'])
            except ValueError:
                raise WeightingError(f'{path.name} row {number}: share is not a number: {row["share"]}') from None
            if not 0 <= share <= 1:
                raise WeightingError(f'{path.name} row {number}: share {share} is outside 0..1')
            cells = targets.setdefault(question, {})
            if option in cells:
                raise WeightingError(f'{path.name} row {number}: {question}={option} is listed twice')
            cells[option] = share
    if not targets:
        raise WeightingError(f'{path.name}: no targets')
    for question, cells in targets.items():
        total = sum(cells.values())
        if abs(total - 1) > SHARE_TOLERANCE:
            raise WeightingError(f'{path.name}: shares for {question} add up to {total:.3f}, not 1')
    return targets
