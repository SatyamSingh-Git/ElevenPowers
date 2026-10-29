"""Desk activity by month, counted from the ledger, for the monthly return to the council."""
from ..model.dates import month_of
from ..model.money import format_money

COUNTED = {'checkout': 'issues', 'renew': 'renewals', 'return': 'returns', 'lost': 'lost',
           'payment': 'payments', 'waive': 'waivers'}
COLUMNS = ('month', 'issues', 'renewals', 'returns', 'lost', 'payments', 'waivers', 'taken')


def activity_rows(entries, year=None):
    """One row per month that had any activity, oldest month first."""
    months = {}
    for entry in entries:
        if year is not None and entry.date.year != year:
            continue
        row = months.setdefault(month_of(entry.date), dict.fromkeys(COLUMNS[1:], 0))
        row[COUNTED[entry.event]] += 1
        if entry.event == 'payment':
            row['taken'] += entry.amount
    return [{'month': month, **counts, 'taken': format_money(counts['taken'])}
            for month, counts in sorted(months.items())]
