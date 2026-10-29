"""The day sheet the desk supervisor signs off at closing time."""
from ..model.dates import format_date
from ..model.money import format_money
from ..services.fines import signed_amount


def day_sheet(library, day):
    """What happened at the desk on `day`, as `label: value` lines."""
    issued = returned = renewed = written_off = 0
    charged = taken = waived = 0
    for entry in library.ledger.entries():
        if entry.date != day:
            continue
        if entry.event == 'checkout':
            issued += 1
        elif entry.event == 'return':
            returned += 1
        elif entry.event == 'renew':
            renewed += 1
        elif entry.event == 'lost':
            written_off += 1
        amount = signed_amount(entry)
        if amount > 0:
            charged += amount
        elif entry.event == 'payment':
            taken -= amount
        elif amount < 0:
            waived -= amount
    joined = sum(member.joined == day for member in library.members.values())
    placed = sum(hold.placed == day for hold in library.holds)
    lines = [
        f'day: {format_date(day)}',
        f'issued: {issued}',
        f'returned: {returned}',
        f'renewed: {renewed}',
        f'written off: {written_off}',
        f'charged: {format_money(charged)}',
        f'taken: {format_money(taken)}',
        f'waived: {format_money(waived)}',
        f'joined: {joined}',
        f'holds placed: {placed}',
    ]
    return '\n'.join(lines) + '\n'
