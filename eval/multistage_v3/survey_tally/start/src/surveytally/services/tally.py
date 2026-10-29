"""Frequency tables: how often each answer was given, weighted or not."""
from collections import Counter
from dataclasses import dataclass

from .weighting import weight_for


@dataclass
class Row:
    code: object
    label: str
    count: int
    weighted: float
    percent: float


@dataclass
class FrequencyTable:
    """One question's answers.

    `base` counts the respondents who answered and `missing` those who did not.
    Percentages are of the weighted base, so they add up to more than 100 for
    multiple-choice questions. Choice questions list their options from most to
    least chosen, scale questions their points from lowest to highest, and
    free-text questions have no rows.
    """

    question_id: str
    text: str
    rows: list
    base: int
    weighted_base: float
    missing: int
    mean: float | None = None

    def row(self, code):
        for row in self.rows:
            if row.code == code:
                return row
        raise KeyError(code)


class Tally:
    """Counts answers question by question; the handler for each question is chosen by its type."""

    def __init__(self, responses, weights=None):
        self.responses = responses
        self.weights = weights

    def table(self, question):
        return getattr(self, f'_tally_{question.type}')(question)

    def _tally_single(self, question):
        counts, weighted, base, weighted_base = self._count(question)
        rows = [self._row(code, question.label_for(code), counts, weighted, weighted_base) for code in question.codes()]
        return self._choice_table(question, rows, base, weighted_base)

    _tally_multi = _tally_single

    def _tally_scale(self, question):
        counts, weighted, base, weighted_base = self._count(question)
        points = question.points()
        rows = [self._row(point, question.label_for(point), counts, weighted, weighted_base) for point in points]
        mean = sum(point * weighted[point] for point in points) / weighted_base if weighted_base else None
        return FrequencyTable(question.id, question.text, rows, base, weighted_base, len(self.responses) - base, mean)

    def _tally_text(self, question):
        _, _, base, weighted_base = self._count(question)
        return FrequencyTable(question.id, question.text, [], base, weighted_base, len(self.responses) - base)

    def _choice_table(self, question, rows, base, weighted_base):
        rows.sort(key=lambda row: row.weighted, reverse=True)
        return FrequencyTable(question.id, question.text, rows, base, weighted_base, len(self.responses) - base)

    def _count(self, question):
        counts, weighted = Counter(), Counter()
        base, weighted_base = 0, 0.0
        for response in self.responses:
            values = response.chosen(question.id)
            if not values:
                continue
            weight = weight_for(self.weights, response.respondent)
            base += 1
            weighted_base += weight
            for value in values:
                counts[value] += 1
                weighted[value] += weight
        return counts, weighted, base, weighted_base

    @staticmethod
    def _row(code, label, counts, weighted, weighted_base):
        percent = 100 * weighted[code] / weighted_base if weighted_base else 0.0
        return Row(code, label, counts[code], float(weighted[code]), percent)


def frequencies(survey, responses, weights=None):
    """A frequency table for every question, keyed by question id, in questionnaire order."""
    tally = Tally(responses, weights)
    return {question.id: tally.table(question) for question in survey.questions}
