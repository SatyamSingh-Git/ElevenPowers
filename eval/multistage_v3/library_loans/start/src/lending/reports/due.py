"""What falls due on a given day, and the slip a member takes home."""
from .._generated import BRANCHES, MATERIALS
from ..model.dates import format_date

DUE_COLUMNS = ('card', 'name', 'barcode', 'title', 'material')


def due_rows(library, day):
    """Loans due back on `day`, grouped by member, for the courtesy phone round."""
    rows = []
    for loan in sorted(library.loans.values(), key=lambda loan: (loan.card, loan.barcode)):
        if loan.due != day:
            continue
        title = library.catalogue.title_of(loan.barcode)
        rows.append({'card': loan.card, 'name': library.members[loan.card].name, 'barcode': loan.barcode,
                     'title': title.title, 'material': MATERIALS[title.material]})
    return rows


def slip(library, card):
    """The printed slip: every item the member has out, soonest due first."""
    member = library.member(card)
    where = BRANCHES.get(library.branch, 'the library')
    lines = [f'{where} - {format_date(library.today())}', f'{member.name} ({member.card})', '']
    loans = library.loans_of(member.card)
    for loan in loans:
        title = library.catalogue.title_of(loan.barcode).title
        lines.append(f'{format_date(loan.due)}  {loan.barcode}  {title}')
    if not loans:
        lines.append('Nothing on loan.')
    lines += ['', 'Renew at any desk, or by phone.']
    return '\n'.join(lines) + '\n'
