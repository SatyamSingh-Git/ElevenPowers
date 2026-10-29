"""Fieldwork progress: responses per day, and how far each quota cell has filled.

Quotas come from a targets file: a cell's quota is its share of the goal,
rounded to whole respondents.
"""
from collections import Counter
from dataclasses import dataclass

UNDATED_LABEL = '(no date)'


@dataclass(frozen=True)
class Day:
    date: str
    count: int
    cumulative: int


@dataclass(frozen=True)
class QuotaCell:
    question: str
    option: str
    quota: int
    achieved: int

    @property
    def remaining(self):
        return max(0, self.quota - self.achieved)

    @property
    def filled(self):
        return self.achieved >= self.quota


def daily_counts(responses):
    """Responses per submission date in date order; undated responses come last."""
    counts = Counter(response.submitted for response in responses)
    days, running = [], 0
    for day in sorted(day for day in counts if day):
        running += counts[day]
        days.append(Day(day, counts[day], running))
    if counts.get(''):
        running += counts['']
        days.append(Day(UNDATED_LABEL, counts[''], running))
    return days


def quota_cells(responses, targets, goal):
    cells = []
    for question_id, shares in targets.items():
        achieved = Counter(response.answer(question_id) for response in responses)
        for option, share in shares.items():
            cells.append(QuotaCell(question_id, option, round(share * goal), achieved[option]))
    return cells


def progress_report(responses, targets=None, goal=None):
    lines = ['date        responses  total']
    for day in daily_counts(responses):
        lines.append(f'{day.date:<10}  {day.count:>9}  {day.cumulative:>5}')
    if targets and goal:
        lines += ['', f'quotas for a goal of {goal}:']
        for cell in quota_cells(responses, targets, goal):
            status = 'full' if cell.filled else f'{cell.remaining} to go'
            lines.append(f'  {cell.question}={cell.option}: {cell.achieved} of {cell.quota} ({status})')
    return '\n'.join(lines) + '\n'
