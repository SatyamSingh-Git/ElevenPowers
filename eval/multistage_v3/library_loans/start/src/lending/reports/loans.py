"""A member's loans, as the desk reads them out: what is due when, and what can be extended."""
from ..model.dates import format_date

COLUMNS = ('barcode', 'title', 'due', 'overdue', 'renewals_left', 'renewable')


def member_loans(library, card):
    member = library.member(card)
    today = library.today()
    rows = []
    for loan in library.loans_of(member.card):
        left = library.settings.max_renewals - loan.renewals
        rows.append({'barcode': loan.barcode, 'title': library.catalogue.title_of(loan.barcode).title,
                     'due': format_date(loan.due), 'overdue': loan.days_overdue(today),
                     'renewals_left': max(0, left), 'renewable': 'yes' if left > 0 else 'no'})
    return rows
