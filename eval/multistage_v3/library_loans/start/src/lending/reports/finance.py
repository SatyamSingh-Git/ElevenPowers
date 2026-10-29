"""Money by day, for finance: what was charged, what was taken and what was waived."""
from ..model.dates import format_date
from ..model.money import format_money
from ..services.fines import signed_amount

COLUMNS = ('date', 'charged', 'taken', 'waived', 'net')


def daily_rows(library, since, until):
    """One row per day between `since` and `until`, inclusive, that moved any money, then a total row."""
    days = {}
    for entry in library.ledger.entries():
        amount = signed_amount(entry)
        if amount == 0 or not since <= entry.date <= until:
            continue
        row = days.setdefault(entry.date, {'charged': 0, 'taken': 0, 'waived': 0})
        if amount > 0:
            row['charged'] += amount
        elif entry.event == 'payment':
            row['taken'] -= amount
        else:
            row['waived'] -= amount
    rows = [{'date': format_date(day), **row} for day, row in sorted(days.items())]
    rows.append({'date': 'total', **{column: sum(row[column] for row in rows) for column in COLUMNS[1:4]}})
    return [_formatted(row) for row in rows]


def _formatted(row):
    net = row['charged'] - row['taken'] - row['waived']
    return {'date': row['date'], 'charged': format_money(row['charged']), 'taken': format_money(row['taken']),
            'waived': format_money(row['waived']), 'net': format_money(net)}
