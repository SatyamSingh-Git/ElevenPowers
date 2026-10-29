"""Significance letters for cross-tabulations.

Each column gets a letter: A, B, C and so on. A cell is marked with the
letters of the columns whose percentage it is significantly above, by a
two-proportion z-test on unweighted counts. Columns with fewer than
`min_base` respondents are neither marked nor compared against.
"""
import math
from string import ascii_uppercase

Z_95 = 1.96
MIN_BASE = 30


def column_letters(columns):
    if len(columns) > len(ascii_uppercase):
        raise ValueError(f'significance letters run out after {len(ascii_uppercase)} columns')
    return {column: ascii_uppercase[index] for index, column in enumerate(columns)}


def z_score(hits_a, base_a, hits_b, base_b):
    """How many standard errors proportion a lies above proportion b."""
    pooled = (hits_a + hits_b) / (base_a + base_b)
    spread = math.sqrt(pooled * (1 - pooled) * (1 / base_a + 1 / base_b))
    if spread == 0:
        return 0.0
    return (hits_a / base_a - hits_b / base_b) / spread


def significance(crosstab, z=Z_95, min_base=MIN_BASE):
    """Letters for every cell, keyed by (row, column); an empty string means no difference found."""
    letters = column_letters(crosstab.columns)
    tested = [column for column in crosstab.columns if crosstab.column_counts[column] >= min_base]
    marks = {}
    for row in crosstab.rows:
        for column in crosstab.columns:
            found = []
            if column in tested:
                for other in tested:
                    if other == column:
                        continue
                    score = z_score(crosstab.counts[(row, column)], crosstab.column_counts[column],
                                    crosstab.counts[(row, other)], crosstab.column_counts[other])
                    if score > z:
                        found.append(letters[other])
            marks[(row, column)] = ''.join(found)
    return marks
