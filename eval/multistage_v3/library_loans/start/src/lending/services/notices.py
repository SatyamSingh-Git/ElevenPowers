"""Overdue reminders and hold-ready notices, written to the outbox once a day.

A member gets an overdue reminder on each of the `notice_days` after an item's
due date, one notice covering every item that reaches a reminder day together.
A courtesy reminder goes out `courtesy_days` before items fall due (0 turns
it off), and a hold-ready notice the day a copy is put aside.
"""
from dataclasses import dataclass
from datetime import date

from ..model.dates import format_date
from ..model.holds import READY
from ..storage.outbox import append_notices, read_outbox
from .holds import collect_by

SUBJECTS = {
    'courtesy': 'Due soon: {count} item(s)',
    'overdue': 'Overdue: {count} item(s)',
    'hold_ready': 'Ready to collect: {title}',
}


@dataclass
class Notice:
    date: date
    card: str
    email: str
    kind: str
    subject: str
    body: str


def overdue_notices(library):
    today = library.today()
    due_a_reminder = {}
    for loan in library.loans.values():
        if loan.days_overdue(today) in library.settings.notice_days:
            due_a_reminder.setdefault(loan.card, []).append(loan)
    notices = []
    for card in sorted(due_a_reminder):
        member = library.members[card]
        loans = sorted(due_a_reminder[card], key=lambda loan: (loan.due, loan.barcode))
        body = [f'Dear {member.name},', '', 'These items are overdue:']
        body += [f'  {library.catalogue.title_of(loan.barcode).title} (due {format_date(loan.due)})' for loan in loans]
        notices.append(Notice(today, card, member.email, 'overdue',
                              SUBJECTS['overdue'].format(count=len(loans)), '\n'.join(body)))
    return notices


def courtesy_notices(library):
    days = library.settings.courtesy_days
    if days == 0:
        return []
    today = library.today()
    falling_due = {}
    for loan in library.loans.values():
        if (loan.due - today).days == days:
            falling_due.setdefault(loan.card, []).append(loan)
    notices = []
    for card in sorted(falling_due):
        member = library.members[card]
        loans = sorted(falling_due[card], key=lambda loan: loan.barcode)
        body = [f'Dear {member.name},', '', f'These items are due back on {format_date(loans[0].due)}:']
        body += [f'  {library.catalogue.title_of(loan.barcode).title}' for loan in loans]
        body += ['', 'You can renew them at any desk.']
        notices.append(Notice(today, card, member.email, 'courtesy',
                              SUBJECTS['courtesy'].format(count=len(loans)), '\n'.join(body)))
    return notices


def hold_ready_notices(library):
    today = library.today()
    notices = []
    for hold in library.holds:
        if hold.status != READY or hold.ready_on != today:
            continue
        member = library.members[hold.card]
        title = library.catalogue.title(hold.title_id).title
        body = (f'Dear {member.name},\n\n{title} is waiting for you at the desk. '
                f'Please collect it by {format_date(collect_by(library, hold))}.')
        notices.append(Notice(today, hold.card, member.email, 'hold_ready',
                              SUBJECTS['hold_ready'].format(title=title), body))
    return notices


def send_notices(library):
    """Write today's notices to the outbox, skipping any already written today."""
    today = format_date(library.today())
    sent = {(record['card'], record['subject']) for record in read_outbox(library.directory)
            if record['date'] == today}
    todays = courtesy_notices(library) + overdue_notices(library) + hold_ready_notices(library)
    fresh = [notice for notice in todays
             if (notice.card, notice.subject) not in sent]
    append_notices(library.directory, fresh)
    return fresh
