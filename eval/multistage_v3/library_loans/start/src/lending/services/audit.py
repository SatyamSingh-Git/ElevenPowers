"""Checking a library directory for records that contradict each other.

The files are written by this tool, but staff do open them in editors, and a
restored backup can be older than the ledger. `lend check` lists every problem
it finds rather than stopping at the first.
"""
from ..model.dates import format_date
from ..model.holds import READY


def check_library(library):
    problems = []
    problems += _check_loans(library)
    problems += _check_holds(library)
    return problems


def _check_loans(library):
    problems = []
    known = {copy.barcode for title in library.catalogue.titles() for copy in title.copies}
    out = {}
    for entry in library.ledger.entries():
        if entry.event not in ('checkout', 'renew', 'return', 'lost'):
            continue
        where = f'{format_date(entry.date)} {entry.event} {entry.barcode}'
        if entry.barcode not in known:
            problems.append(f'{where}: barcode not in the catalogue')
            continue
        if entry.card not in library.members:
            problems.append(f'{where}: card {entry.card} is not a member')
        if entry.event == 'checkout':
            if entry.barcode in out:
                problems.append(f'{where}: already on loan to {out[entry.barcode]}')
            out[entry.barcode] = entry.card
        elif entry.barcode not in out:
            problems.append(f'{where}: not on loan at the time')
        elif entry.event in ('return', 'lost'):
            del out[entry.barcode]
    return problems


def _check_holds(library):
    problems = []
    titles = {title.id for title in library.catalogue.titles()}
    seen = set()
    for hold in library.holds:
        where = f'hold on {hold.title_id} for {hold.card}'
        if hold.card not in library.members:
            problems.append(f'{where}: not a member')
        if hold.title_id not in titles:
            problems.append(f'{where}: title not in the catalogue')
        if (hold.card, hold.title_id) in seen:
            problems.append(f'{where}: placed twice')
        seen.add((hold.card, hold.title_id))
        if hold.status == READY and hold.barcode in library.loans:
            problems.append(f'{where}: copy {hold.barcode} is set aside but out on loan')
    return problems
